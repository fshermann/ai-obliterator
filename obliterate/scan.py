"""Match rules, report findings, and rewrite files."""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from obliterate.config import Config, default_config, load_config, resolve_config_path
from obliterate.errors import ObliterateError
from obliterate.rules import Rule


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    column: int
    rule: str
    snippet: str


def execute(args: argparse.Namespace, *, write: bool) -> int:
    config_path = resolve_config_path(getattr(args, "config", None))
    config = default_config() if config_path is None else load_config(config_path)
    raw_paths = list(args.paths) or ["."]
    if "-" in raw_paths:
        if raw_paths != ["-"]:
            raise ObliterateError("stdin cannot be combined with other paths")
        return _process_stdin(config, write=write, output_format=args.format)
    files = collect_files(raw_paths, config)
    findings: list[Finding] = []
    changed: list[str] = []
    for path in files:
        original = read_text(path)
        label = display_path(path)
        if original is None:
            print(f"ai-obliterator: skipped binary file: {label}", file=sys.stderr)
            continue
        updated, found = transform(original, config.rules)
        findings.extend(_to_findings(label, original, found))
        if write and updated != original:
            _write_atomic(path, updated)
            changed.append(label)
    findings.sort(key=lambda item: (item.path, item.line, item.column))
    changed.sort()
    return _report(findings, changed, write=write, output_format=args.format)


def collect_files(raw_paths: list[str], config: Config) -> list[Path]:
    found: list[Path] = []
    seen: set[Path] = set()
    for raw in raw_paths:
        path = Path(raw)
        if not path.exists():
            raise ObliterateError(f"path not found: {raw}")
        if path.is_file():
            _add_file(found, seen, path, config, explicit=True)
        elif path.is_dir():
            try:
                children = _walk_files(path, config)
            except OSError as exc:
                target = exc.filename or raw
                raise ObliterateError(f"cannot read {target}: {exc.strerror}") from exc
            for child in children:
                _add_file(found, seen, child, config, explicit=False)
        else:
            raise ObliterateError(f"not a file or directory: {raw}")
    return found


def transform(text: str, rules: tuple[Rule, ...] | list[Rule]) -> tuple[str, list[tuple[int, str, str]]]:
    index_map = list(range(len(text) + 1))
    found: list[tuple[int, str, str]] = []
    for rule in rules:
        matches = list(rule.pattern.finditer(text))
        if not matches:
            continue
        pieces: list[str] = []
        new_map: list[int] = []
        cursor = 0
        for match in matches:
            start = match.start()
            end = match.end()
            if start < cursor:
                continue
            pieces.append(text[cursor:start])
            new_map.extend(index_map[cursor:start])
            replacement = _replacement(rule, match)
            if replacement != match.group(0):
                found.append((index_map[start], rule.id, match.group(0)))
            pieces.append(replacement)
            origin = index_map[start]
            new_map.extend([origin] * len(replacement))
            cursor = end
        pieces.append(text[cursor:])
        new_map.extend(index_map[cursor:])
        updated = "".join(pieces)
        if len(new_map) != len(updated) + 1:
            raise ObliterateError(f"rule {rule.id}: internal alignment error")
        text = updated
        index_map = new_map
    return text, found


def read_text(path: Path) -> str | None:
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise ObliterateError(f"cannot read {path}: {exc.strerror}") from exc
    if b"\0" in data:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except (OSError, ValueError):
        return path.as_posix()


def _process_stdin(config: Config, *, write: bool, output_format: str) -> int:
    original = _read_stdin()
    updated, found = transform(original, config.rules)
    findings = _to_findings("<stdin>", original, found)
    findings.sort(key=lambda item: (item.line, item.column))
    if write:
        sys.stdout.write(updated)
        return 0
    return _report(findings, [], write=False, output_format=output_format)


def _read_stdin() -> str:
    stream = sys.stdin
    reconfigure = getattr(stream, "reconfigure", None)
    if reconfigure is not None:
        try:
            reconfigure(newline="")
        except (OSError, ValueError):
            pass
    return stream.read()


def _walk_files(directory: Path, config: Config) -> list[Path]:
    files: list[Path] = []
    scan_root = directory.resolve()
    project_root = config.project_root.resolve()
    for dirpath, dirnames, filenames in os.walk(directory):
        current = Path(dirpath)
        rel_dir = _relative_key(current, project_root, scan_root)
        kept: list[str] = []
        for name in sorted(dirnames):
            child_rel = f"{rel_dir}/{name}" if rel_dir else name
            if not _dir_excluded(child_rel, config):
                kept.append(name)
        dirnames[:] = kept
        for name in sorted(filenames):
            rel = f"{rel_dir}/{name}" if rel_dir else name
            path = current / name
            if _is_config_file(path, config) or _excluded(rel, config):
                continue
            if config.include_patterns and not _matches(rel, config.include_patterns):
                continue
            files.append(path)
    return files


def _add_file(
    found: list[Path],
    seen: set[Path],
    path: Path,
    config: Config,
    *,
    explicit: bool,
) -> None:
    if not explicit and _is_config_file(path, config):
        return
    try:
        key = path.resolve()
    except OSError as exc:
        raise ObliterateError(f"cannot read {path}: {exc.strerror}") from exc
    if key in seen:
        return
    seen.add(key)
    found.append(path)


def _relative_key(path: Path, project_root: Path, scan_root: Path) -> str:
    resolved = path.resolve()
    try:
        relative = resolved.relative_to(project_root).as_posix()
    except ValueError:
        relative = resolved.relative_to(scan_root).as_posix()
    if relative == ".":
        return ""
    return relative


def _dir_excluded(relative: str, config: Config) -> bool:
    if _matches(relative, config.exclude_patterns):
        return True
    return _matches(relative, config.exclude_dir_bases)


def _excluded(relative: str, config: Config) -> bool:
    return _matches(relative, config.exclude_patterns)


def _matches(relative: str, patterns: tuple[re.Pattern[str], ...]) -> bool:
    return any(pattern.search(relative) for pattern in patterns)


def _is_config_file(path: Path, config: Config) -> bool:
    if config.source is None:
        return False
    try:
        return path.resolve() == config.source
    except OSError:
        return False


def _replacement(rule: Rule, match: re.Match[str]) -> str:
    if rule.literal:
        return rule.replacement
    try:
        return match.expand(rule.replacement)
    except re.error as exc:
        raise ObliterateError(f"rule {rule.id}: invalid replacement: {exc}") from exc


def _to_findings(
    path_label: str,
    original: str,
    found: list[tuple[int, str, str]],
) -> list[Finding]:
    findings: list[Finding] = []
    for origin, rule_id, snippet in found:
        line, column = line_column(original, origin)
        findings.append(
            Finding(
                path=path_label,
                line=line,
                column=column,
                rule=rule_id,
                snippet=visible(snippet),
            )
        )
    return findings


def line_column(text: str, index: int) -> tuple[int, int]:
    if index < 0:
        index = 0
    if index > len(text):
        index = len(text)
    line = text.count("\n", 0, index) + 1
    last_break = text.rfind("\n", 0, index)
    return line, index - last_break


def visible(text: str) -> str:
    parts: list[str] = []
    for char in text:
        category = unicodedata.category(char)
        if char == " ":
            parts.append(char)
        elif category.startswith(("C", "Z")):
            parts.append(f"\\u{ord(char):04x}")
        else:
            parts.append(char)
    rendered = "".join(parts)
    if len(rendered) > 80:
        return rendered[:77] + "..."
    return rendered


def _write_atomic(path: Path, text: str) -> None:
    temporary = path.with_name(path.name + ".obliterator-tmp")
    try:
        temporary.write_text(text, encoding="utf-8", newline="")
        os.chmod(temporary, stat.S_IMODE(path.stat().st_mode))
        os.replace(temporary, path)
    except OSError as exc:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        raise ObliterateError(f"cannot write {path}: {exc.strerror}") from exc


def _report(
    findings: list[Finding],
    changed: list[str],
    *,
    write: bool,
    output_format: str,
) -> int:
    failed = (not write) and bool(findings)
    if output_format == "json":
        payload: dict[str, object] = {
            "ok": not failed,
            "findings": [
                {
                    "path": item.path,
                    "line": item.line,
                    "column": item.column,
                    "rule": item.rule,
                    "snippet": item.snippet,
                }
                for item in findings
            ],
        }
        if write:
            payload["changed"] = changed
        sys.stdout.write(json.dumps(payload, indent=2, ensure_ascii=True) + "\n")
    elif write:
        if changed:
            sys.stdout.write("\n".join(changed) + "\n")
    elif findings:
        lines = [
            f"{item.path}:{item.line}:{item.column}: {item.rule}: {item.snippet}"
            for item in findings
        ]
        sys.stdout.write("\n".join(lines) + "\n")
    return 1 if failed else 0
