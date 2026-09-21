"""Load exodia.yml and discover it from the working directory."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from obliterate.errors import ObliterateError
from obliterate.rules import CustomRule, Rule, RuleOverride, compile_rules

DEFAULT_EXCLUDES: tuple[str, ...] = (
    ".git/**",
    ".venv/**",
    "venv/**",
    "__pycache__/**",
    "dist/**",
    "build/**",
    "*.egg-info/**",
)

_TOP_LEVEL = {"version", "include", "exclude", "rules", "custom"}
_OVERRIDE_KEYS = {"enabled", "replacement"}
_CUSTOM_KEYS = {"id", "pattern", "replacement", "enabled"}
_REQUIRED_CUSTOM = {"id", "pattern", "replacement"}


@dataclass
class Config:
    project_root: Path
    source: Path | None
    include: tuple[str, ...]
    exclude: tuple[str, ...]
    include_patterns: tuple[re.Pattern[str], ...]
    exclude_patterns: tuple[re.Pattern[str], ...]
    exclude_dir_bases: tuple[re.Pattern[str], ...]
    rules: tuple[Rule, ...]


def resolve_config_path(explicit: str | None, cwd: Path | None = None) -> Path | None:
    if explicit is not None:
        path = Path(explicit)
        if not path.is_file():
            raise ObliterateError(f"config not found: {explicit}")
        return path
    current = (cwd or Path.cwd()).resolve()
    for directory in (current, *current.parents):
        candidate = directory / "exodia.yml"
        if candidate.is_file():
            return candidate
    return None


def default_config(project_root: Path | None = None) -> Config:
    root = (project_root or Path.cwd()).resolve()
    return _assemble(
        project_root=root,
        source=None,
        include=(),
        exclude=DEFAULT_EXCLUDES,
        overrides={},
        custom=[],
    )


def load_config(path: Path) -> Config:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ObliterateError(f"invalid config: {path} is not utf-8") from exc
    except OSError as exc:
        raise ObliterateError(f"cannot read config: {exc.strerror}") from exc

    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ObliterateError(f"invalid config: {exc}") from exc

    if not isinstance(data, dict):
        raise ObliterateError("config must be a mapping")

    unknown = sorted(set(data) - _TOP_LEVEL)
    if unknown:
        names = ", ".join(unknown)
        raise ObliterateError(f"unknown config keys: {names}")

    version = data.get("version")
    if version not in (1, "1"):
        raise ObliterateError("config version must be 1")

    include = _string_list(data.get("include"), "include")
    exclude = _dedupe((*DEFAULT_EXCLUDES, *_string_list(data.get("exclude"), "exclude")))
    overrides = _parse_overrides(data.get("rules", {}))
    custom = _parse_custom(data.get("custom", []))
    return _assemble(
        project_root=path.resolve().parent,
        source=path.resolve(),
        include=tuple(include),
        exclude=tuple(exclude),
        overrides=overrides,
        custom=custom,
    )


def _assemble(
    *,
    project_root: Path,
    source: Path | None,
    include: tuple[str, ...],
    exclude: tuple[str, ...],
    overrides: dict[str, RuleOverride],
    custom: list[CustomRule],
) -> Config:
    include_patterns = tuple(glob_to_regex(pattern) for pattern in include)
    exclude_patterns, exclude_dir_bases = _compile_excludes(exclude)
    return Config(
        project_root=project_root,
        source=source,
        include=include,
        exclude=exclude,
        include_patterns=include_patterns,
        exclude_patterns=exclude_patterns,
        exclude_dir_bases=exclude_dir_bases,
        rules=tuple(compile_rules(overrides, custom)),
    )


def _parse_overrides(raw: object) -> dict[str, RuleOverride]:
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise ObliterateError("rules must be a mapping")
    overrides: dict[str, RuleOverride] = {}
    for rule_id, body in raw.items():
        if not isinstance(rule_id, str):
            raise ObliterateError("rule ids must be strings")
        if body is None:
            body = {}
        if not isinstance(body, dict):
            raise ObliterateError(f"rule {rule_id} must be a mapping")
        unknown = sorted(set(body) - _OVERRIDE_KEYS)
        if unknown:
            names = ", ".join(unknown)
            raise ObliterateError(f"rule {rule_id}: unknown keys: {names}")
        enabled = body.get("enabled")
        if enabled is not None and not isinstance(enabled, bool):
            raise ObliterateError(f"rule {rule_id}: enabled must be a boolean")
        replacement = body.get("replacement")
        if "replacement" in body and not isinstance(replacement, str):
            raise ObliterateError(f"rule {rule_id}: replacement must be a string")
        overrides[rule_id] = RuleOverride(
            enabled=enabled if isinstance(enabled, bool) else None,
            replacement=replacement if isinstance(replacement, str) else None,
        )
    return overrides


def _parse_custom(raw: object) -> list[CustomRule]:
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise ObliterateError("custom must be a list")
    custom: list[CustomRule] = []
    for index, body in enumerate(raw, start=1):
        if not isinstance(body, dict):
            raise ObliterateError(f"custom rule {index} must be a mapping")
        unknown = sorted(set(body) - _CUSTOM_KEYS)
        if unknown:
            names = ", ".join(unknown)
            raise ObliterateError(f"custom rule {index}: unknown keys: {names}")
        missing = sorted(_REQUIRED_CUSTOM - set(body))
        if missing:
            names = ", ".join(missing)
            raise ObliterateError(f"custom rule {index}: missing keys: {names}")
        rule_id = body["id"]
        pattern = body["pattern"]
        replacement = body["replacement"]
        enabled = body.get("enabled", True)
        if not isinstance(rule_id, str):
            raise ObliterateError(f"custom rule {index}: id must be a string")
        if not isinstance(pattern, str):
            raise ObliterateError(f"custom rule {rule_id}: pattern must be a string")
        if not isinstance(replacement, str):
            raise ObliterateError(f"custom rule {rule_id}: replacement must be a string")
        if not isinstance(enabled, bool):
            raise ObliterateError(f"custom rule {rule_id}: enabled must be a boolean")
        custom.append(
            CustomRule(
                id=rule_id,
                pattern=pattern,
                replacement=replacement,
                enabled=enabled,
            )
        )
    return custom


def _string_list(raw: object, field: str) -> list[str]:
    if raw is None:
        return []
    if not isinstance(raw, list) or not all(isinstance(item, str) for item in raw):
        raise ObliterateError(f"{field} must be a list of strings")
    return list(raw)


def _dedupe(items: tuple[str, ...] | list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def _compile_excludes(
    patterns: tuple[str, ...],
) -> tuple[tuple[re.Pattern[str], ...], tuple[re.Pattern[str], ...]]:
    compiled: list[re.Pattern[str]] = []
    bases: list[re.Pattern[str]] = []
    for pattern in patterns:
        normalized = _normalize_glob(pattern)
        compiled.append(glob_to_regex(normalized))
        stripped = normalized.rstrip("/")
        if stripped.endswith("/**"):
            base = stripped[:-3]
            if base:
                bases.append(glob_to_regex(base))
    return tuple(compiled), tuple(bases)


def glob_to_regex(pattern: str) -> re.Pattern[str]:
    normalized = _normalize_glob(pattern)
    pieces: list[str] = []
    index = 0
    while index < len(normalized):
        if normalized.startswith("**/", index):
            pieces.append("(?:.*/)?")
            index += 3
        elif normalized.startswith("**", index):
            pieces.append(".*")
            index += 2
        elif normalized[index] == "*":
            pieces.append("[^/]*")
            index += 1
        elif normalized[index] == "?":
            pieces.append("[^/]")
            index += 1
        else:
            pieces.append(re.escape(normalized[index]))
            index += 1
    return re.compile(r"\A" + "".join(pieces) + r"\Z")


def _normalize_glob(pattern: str) -> str:
    normalized = pattern.replace("\\", "/").strip()
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized
