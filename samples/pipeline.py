"""Copy the fixtures, autofix them with Semgrep, then check the result."""

from __future__ import annotations

import difflib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "semgrep" / "ai-artifacts.yml"
FIXTURES = ("before.py", "before.js", "before.ts", "before.tf")


def main() -> int:
    semgrep = _semgrep_command()
    with tempfile.TemporaryDirectory() as tmp:
        workspace = Path(tmp)
        for name in FIXTURES:
            shutil.copyfile(ROOT / "samples" / name, workspace / name)
        for _ in range(3):
            before = _snapshot(workspace)
            completed = subprocess.run(
                [
                    *semgrep,
                    "scan",
                    "--config",
                    str(RULES),
                    "--autofix",
                    "--metrics=off",
                    str(workspace),
                ],
                cwd=ROOT,
            )
            if completed.returncode not in (0, 1):
                return completed.returncode
            if _snapshot(workspace) == before:
                break
        check = subprocess.run(
            [
                *semgrep,
                "scan",
                "--config",
                str(RULES),
                "--error",
                "--metrics=off",
                str(workspace),
            ],
            cwd=ROOT,
        )
        if check.returncode != 0:
            return check.returncode
        for name in FIXTURES:
            expected_path = ROOT / "samples" / name.replace("before", "after")
            expected = expected_path.read_bytes()
            actual = (workspace / name).read_bytes()
            if actual != expected:
                sys.stderr.writelines(
                    difflib.unified_diff(
                        expected.decode("utf-8").splitlines(keepends=True),
                        actual.decode("utf-8").splitlines(keepends=True),
                        fromfile=str(expected_path.relative_to(ROOT)),
                        tofile=name,
                    )
                )
                return 1
    return _check_phrases(semgrep)


def _semgrep_command() -> list[str]:
    directories = [Path(sys.executable).parent, Path(sys.prefix) / "bin", Path(sys.prefix) / "Scripts"]
    found = shutil.which("semgrep")
    if found:
        directories.insert(0, Path(found).parent)
    for directory in directories:
        for name in ("semgrep", "semgrep.exe"):
            candidate = directory / name
            if candidate.is_file():
                return [str(candidate)]
    return ["semgrep"]


def _check_phrases(semgrep: list[str]) -> int:
    source = ROOT / "samples" / "phrases.py"
    expected = _phrase_sections(source)
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / source.name
        shutil.copyfile(source, target)
        completed = subprocess.run(
            [
                *semgrep,
                "scan",
                "--config",
                str(RULES),
                "--json",
                "--quiet",
                "--metrics=off",
                str(target),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
    if completed.returncode not in (0, 1):
        sys.stderr.write(completed.stderr)
        return completed.returncode
    findings = json.loads(completed.stdout)["results"]
    by_line: dict[int, list[dict]] = {}
    for finding in findings:
        by_line.setdefault(finding["start"]["line"], []).append(finding)
    failed = False
    for line, text in expected["ERRORS"]:
        rules = _rules(by_line.get(line, []))
        if text == "del" "ve into":
            wanted = {"no-ai-phrase"}
        else:
            wanted = {"ai-phrase"}
        if rules != wanted:
            sys.stderr.write(f"{source.name}:{line}: {text!r} matched {sorted(rules)}, wanted {sorted(wanted)}\n")
            failed = True
    for line, text in expected["WARNINGS"]:
        rules = _rules(by_line.get(line, []))
        if text.casefold() == "in the ever" "-evolving":
            wanted = {"ai-wording", "ai-phrase"}
        else:
            wanted = {"ai-wording"}
        if "\u2019" in text:
            wanted.add("smart-single-quotes")
        if rules != wanted:
            sys.stderr.write(f"{source.name}:{line}: {text!r} matched {sorted(rules)}, wanted {sorted(wanted)}\n")
            failed = True
    for line, text in expected["CLEAN"]:
        rules = _rules(by_line.get(line, []))
        if rules:
            sys.stderr.write(f"{source.name}:{line}: {text!r} matched {sorted(rules)}\n")
            failed = True
    return 1 if failed else 0


def _phrase_sections(path: Path) -> dict[str, list[tuple[int, str]]]:
    sections: dict[str, list[tuple[int, str]]] = {"ERRORS": [], "WARNINGS": [], "CLEAN": []}
    current = None
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if stripped.endswith("= ("):
            current = stripped.split("=", 1)[0].strip()
            continue
        if current is None or not (stripped.startswith('"') and stripped.endswith('",')):
            continue
        sections[current].append((number, stripped[1:-2]))
    return sections


def _rules(findings: list[dict]) -> set[str]:
    return {finding["check_id"].rsplit(".", 1)[-1] for finding in findings}


def _snapshot(directory: Path) -> dict[str, bytes]:
    return {path.name: path.read_bytes() for path in sorted(directory.iterdir())}


if __name__ == "__main__":
    raise SystemExit(main())
