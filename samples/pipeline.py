"""Copy the fixtures, autofix them with Semgrep, then check the result."""

from __future__ import annotations

import difflib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "semgrep"
FIXTURES = ("before.py", "before.js", "before.ts", "before.tf", "before.cpp")
COMMENT_FIXTURES = ("comments.py", "comments.js", "comments.ts", "comments.tf", "comments.cpp")
STYLE_FIXTURES = ("style.py", "long_file.py")
COMMENT_RULES = {"long-line-comment", "long-block-comment"}
ARTIFACT_RULES = {
    "em-dash",
    "en-dash",
    "horizontal-bar",
    "minus-sign",
    "ellipsis",
    "smart-double-quotes",
    "smart-single-quotes",
    "nbsp",
    "zero-width",
    "emoji",
    "no-ai-phrase",
    "ai-phrase",
    "ai-wording",
    "fix-padding",
    "long-line-comment",
    "long-block-comment",
}

def main() -> int:
    """Run autofix, then the fixture checks. Args: none. Returns: int status."""
    semgrep = _semgrep_command()
    status = _check_autofix(semgrep)
    if status != 0:
        return status
    status = _check_phrases(semgrep)
    if status != 0:
        return status
    status = _check_comments(semgrep)
    if status != 0:
        return status
    return _check_style(semgrep)

def _semgrep_command() -> list[str]:
    """Find the semgrep binary. Args: none. Returns: list command."""
    found = shutil.which("semgrep")
    directories = _command_directories(found)
    return _search_commands(directories, 0)

def _command_directories(found: str | None) -> tuple[Path, ...]:
    """List directories that may hold semgrep. Args: found. Returns: tuple paths."""
    base = (Path(sys.executable).parent, Path(sys.prefix) / "bin", Path(sys.prefix) / "Scripts")
    if found is None:
        return base
    return (Path(found).parent, *base)

def _search_commands(directories: tuple[Path, ...], index: int) -> list[str]:
    """Search one directory, then the next. Args: directories, index. Returns: list command."""
    if index >= len(directories):
        return ["semgrep"]
    found = _directory_command(directories[index])
    if found is not None:
        return found
    return _search_commands(directories, index + 1)

def _directory_command(directory: Path) -> list[str] | None:
    """Look for semgrep in one directory. Args: directory. Returns: list command or none."""
    candidate = directory / "semgrep"
    if candidate.is_file():
        return [str(candidate)]
    other = directory / "semgrep.exe"
    if other.is_file():
        return [str(other)]
    return None

def _check_autofix(semgrep: list[str]) -> int:
    """Autofix the before fixtures and compare them. Args: semgrep. Returns: int status."""
    with tempfile.TemporaryDirectory() as temporary:
        return _autofix_workspace(semgrep, Path(temporary))

def _autofix_workspace(semgrep: list[str], workspace: Path) -> int:
    """Copy, autofix, check, and compare. Args: semgrep, workspace. Returns: int status."""
    _copy_named(FIXTURES, workspace)
    status = _autofix_passes(semgrep, workspace, 3)
    if status != 0:
        return status
    completed = _run_scan(semgrep, workspace, ("--error",), False)
    if completed.returncode != 0:
        return completed.returncode
    return _compare_named(FIXTURES, workspace)

def _autofix_passes(semgrep: list[str], workspace: Path, remaining: int) -> int:
    """Autofix until the files stop changing. Args: semgrep, workspace, remaining. Returns: int status."""
    if remaining == 0:
        return 0
    before = _snapshot(workspace)
    completed = _run_autofix(semgrep, workspace)
    if completed.returncode not in (0, 1):
        return completed.returncode
    if _snapshot(workspace) == before:
        return 0
    return _autofix_passes(semgrep, workspace, remaining - 1)

def _run_autofix(semgrep: list[str], workspace: Path) -> subprocess.CompletedProcess[str]:
    """Autofix one pass. Args: semgrep, workspace. Returns: CompletedProcess result."""
    command = [*semgrep, "scan", "--config", str(RULES), "--autofix", "--metrics=off", str(workspace)]
    return subprocess.run(command, cwd=ROOT)

def _run_scan(
    semgrep: list[str], target: Path, extra: tuple[str, ...], capture: bool
) -> subprocess.CompletedProcess[str]:
    """Run one semgrep scan. Args: semgrep, target, extra, capture. Returns: CompletedProcess result."""
    command = [*semgrep, "scan", "--config", str(RULES), *extra, "--metrics=off", str(target)]
    if capture:
        return subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    return subprocess.run(command, cwd=ROOT)

def _copy_named(names: tuple[str, ...], workspace: Path) -> None:
    """Copy sample files into the workspace. Args: names, workspace. Returns: none."""
    for name in names:
        shutil.copyfile(ROOT / "samples" / name, workspace / name)

def _compare_named(names: tuple[str, ...], workspace: Path) -> int:
    """Compare autofixed files with the after fixtures. Args: names, workspace. Returns: int status."""
    statuses = [_compare_one(name, workspace) for name in names]
    return _first_failure(statuses)

def _compare_one(name: str, workspace: Path) -> int:
    """Diff one autofixed fixture against its after file. Args: name, workspace. Returns: int status."""
    expected_path = ROOT / "samples" / name.replace("before", "after")
    expected = expected_path.read_bytes()
    actual = (workspace / name).read_bytes()
    return _report_diff(expected_path, name, expected, actual)

def _report_diff(expected_path: Path, name: str, expected: bytes, actual: bytes) -> int:
    """Write a diff when the bytes differ. Args: expected_path, name, expected, actual. Returns: int status."""
    if actual == expected:
        return 0
    sys.stderr.writelines(
        difflib.unified_diff(
            expected.decode("utf-8").splitlines(keepends=True),
            actual.decode("utf-8").splitlines(keepends=True),
            fromfile=str(expected_path.relative_to(ROOT)),
            tofile=name,
        )
    )
    return 1

def _snapshot(directory: Path) -> dict[str, bytes]:
    """Read every file in a directory. Args: directory. Returns: dict bytes."""
    captured = {path.name: path.read_bytes() for path in sorted(directory.iterdir())}
    return captured

def _first_failure(statuses: list[int]) -> int:
    """Return the first nonzero status. Args: statuses. Returns: int status."""
    failed = [status for status in statuses if status != 0]
    if failed:
        return failed[0]
    return 0

def _check_phrases(semgrep: list[str]) -> int:
    """Check phrase fixtures against the expected rules. Args: semgrep. Returns: int status."""
    source = ROOT / "samples" / "phrases.py"
    expected = _phrase_sections(source)
    code, findings = _scan_copy(semgrep, source)
    if code != 0:
        return code
    grouped = _line_findings(findings)
    failed = _check_phrase_rows(source, expected["ERRORS"], grouped, _error_wanted)
    failed = _combine_failed(failed, _check_phrase_rows(source, expected["WARNINGS"], grouped, _warning_wanted))
    failed = _combine_failed(failed, _check_phrase_rows(source, expected["CLEAN"], grouped, _clean_wanted))
    return _failed_status(failed)

def _phrase_sections(path: Path) -> dict[str, list[tuple[int, str]]]:
    """Split phrases.py into ERRORS, WARNINGS, and CLEAN. Args: path. Returns: dict sections."""
    sections: dict[str, list[tuple[int, str]]] = {"ERRORS": [], "WARNINGS": [], "CLEAN": []}
    state = {"current": None}
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        _phrase_line(line, sections, state, number)
    return sections

def _phrase_line(line: str, sections: dict[str, list[tuple[int, str]]], state: dict, number: int) -> None:
    """Record one phrase row. Args: line, sections, state, number. Returns: none."""
    stripped = line.strip()
    if stripped.endswith("= ("):
        state["current"] = stripped.split("=", 1)[0].strip()
        return
    _maybe_phrase(stripped, sections, state["current"], number)

def _maybe_phrase(stripped: str, sections: dict[str, list[tuple[int, str]]], current: str | None, number: int) -> None:
    """Append a quoted phrase row. Args: stripped, sections, current, number. Returns: none."""
    if current is None:
        return
    if not (stripped.startswith('"') and stripped.endswith('",')):
        return
    sections[current].append((number, stripped[1:-2]))

def _check_phrase_rows(source: Path, rows: list[tuple[int, str]], grouped: dict[int, list], wanted_for) -> bool:
    """Check one phrase section. Args: source, rows, grouped, wanted_for. Returns: bool failed."""
    flags = [_check_phrase_row(source, number, text, grouped, wanted_for) for number, text in rows]
    return _any_failed(flags)

def _check_phrase_row(source: Path, number: int, text: str, grouped: dict[int, list], wanted_for) -> bool:
    """Compare one phrase line. Args: source, number, text, grouped, wanted_for. Returns: bool failed."""
    rules = _artifact_rules(grouped.get(number, []))
    wanted = wanted_for(text)
    return _report_phrase(source, number, text, rules, wanted)

def _error_wanted(text: str) -> set[str]:
    """Expected error rules for one phrase. Args: text. Returns: set rules."""
    if text == "del" "ve into":
        return {"no-ai-phrase"}
    return {"ai-phrase"}

def _warning_wanted(text: str) -> set[str]:
    """Expected warning rules for one phrase. Args: text. Returns: set rules."""
    if text.casefold() == "in the ever" "-evolving":
        wanted = {"ai-wording", "ai-phrase"}
    else:
        wanted = {"ai-wording"}
    return _with_smart_quote(text, wanted)

def _with_smart_quote(text: str, wanted: set[str]) -> set[str]:
    """Add the smart-quote rule when the phrase has one. Args: text, wanted. Returns: set rules."""
    if "\u2019" in text:
        wanted.add("smart-single-quotes")
    return wanted

def _clean_wanted(text: str) -> set[str]:
    """Expected rules for a clean phrase line. Args: text. Returns: set rules."""
    kept = set()
    return kept

def _report_phrase(source: Path, number: int, text: str, rules: set[str], wanted: set[str]) -> bool:
    """Write a phrase mismatch. Args: source, number, text, rules, wanted. Returns: bool failed."""
    if rules == wanted:
        return False
    if wanted:
        sys.stderr.write(
            f"{source.name}:{number}: {text!r} matched {sorted(rules)}, wanted {sorted(wanted)}\n"
        )
        return True
    sys.stderr.write(f"{source.name}:{number}: {text!r} matched {sorted(rules)}\n")
    return True

def _artifact_rules(findings: list) -> set[str]:
    """Keep artifact rule ids from one line. Args: findings. Returns: set rules."""
    names = {finding["check_id"].rsplit(".", 1)[-1] for finding in findings}
    kept = {name for name in names if name in ARTIFACT_RULES}
    return kept

def _line_findings(findings: list) -> dict[int, list]:
    """Group findings by start line. Args: findings. Returns: dict findings."""
    grouped: dict[int, list] = {}
    for finding in findings:
        grouped.setdefault(finding["start"]["line"], []).append(finding)
    return grouped

def _check_comments(semgrep: list[str]) -> int:
    """Check long-comment fixtures. Args: semgrep. Returns: int status."""
    statuses = [_check_comment_file(name, semgrep) for name in COMMENT_FIXTURES]
    return _first_failure(statuses)

def _check_comment_file(name: str, semgrep: list[str]) -> int:
    """Check one comment fixture. Args: name, semgrep. Returns: int status."""
    source = ROOT / "samples" / name
    code, findings = _scan_copy(semgrep, source)
    if code != 0:
        return code
    lines = source.read_text(encoding="utf-8").splitlines()
    covered: dict[int, set[str]] = {}
    failed = _record_comment_findings(name, findings, lines, covered)
    failed = _combine_failed(failed, _expect_comment_lines(name, lines, covered))
    return _failed_status(failed)

def _record_comment_findings(name: str, findings: list, lines: list[str], covered: dict[int, set[str]]) -> bool:
    """Record comment findings and reject other artifact rules. Args: name, findings, lines, covered. Returns: bool failed."""
    flags = [_record_comment_finding(name, finding, lines, covered) for finding in findings]
    return _any_failed(flags)

def _record_comment_finding(name: str, finding: dict, lines: list[str], covered: dict[int, set[str]]) -> bool:
    """Record one finding. Args: name, finding, lines, covered. Returns: bool failed."""
    rule = finding["check_id"].rsplit(".", 1)[-1]
    if rule not in ARTIFACT_RULES:
        return False
    return _record_artifact_comment(name, finding, lines, covered, rule)

def _record_artifact_comment(
    name: str, finding: dict, lines: list[str], covered: dict[int, set[str]], rule: str
) -> bool:
    """Keep long-comment findings and reject other artifact rules. Args: name, finding, lines, covered, rule. Returns: bool failed."""
    if rule not in COMMENT_RULES:
        sys.stderr.write(f"{name}:{finding['start']['line']}: unexpected {rule}\n")
        return True
    failed = _comment_severity(name, finding, rule)
    _cover_lines(covered, finding["start"]["line"], finding["end"]["line"], rule)
    return _combine_failed(failed, _comment_token(name, finding, lines, rule))

def _comment_severity(name: str, finding: dict, rule: str) -> bool:
    """Require ERROR on a comment finding. Args: name, finding, rule. Returns: bool failed."""
    severity = finding["extra"]["severity"]
    if severity == "ERROR":
        return False
    sys.stderr.write(f"{name}:{finding['start']['line']}: {rule} severity {severity}\n")
    return True

def _comment_token(name: str, finding: dict, lines: list[str], rule: str) -> bool:
    """Require the marker inside the finding span. Args: name, finding, lines, rule. Returns: bool failed."""
    start = finding["start"]["line"]
    end_line = finding["end"]["line"]
    token = "LONG_LINE" if rule == "long-line-comment" else "LONG_BLOCK"
    span = "\n".join(lines[start - 1:end_line])
    if token in span:
        return False
    sys.stderr.write(f"{name}:{start}: unexpected {rule}\n")
    return True

def _cover_lines(covered: dict[int, set[str]], start: int, end_line: int, rule: str) -> None:
    """Mark lines covered by one finding. Args: covered, start, end_line, rule. Returns: none."""
    for number in range(start, end_line + 1):
        covered.setdefault(number, set()).add(rule)

def _expect_comment_lines(name: str, lines: list[str], covered: dict[int, set[str]]) -> bool:
    """Check markers on each line. Args: name, lines, covered. Returns: bool failed."""
    pairs = list(enumerate(lines, start=1))
    flags = [_expect_comment_line(name, text, covered.get(number, set()), number) for number, text in pairs]
    return _any_failed(flags)

def _expect_comment_line(name: str, text: str, rules: set[str], number: int) -> bool:
    """Check one comment marker line. Args: name, text, rules, number. Returns: bool failed."""
    failed = _expect_token(name, text, rules, number, "LONG_LINE", "long-line-comment")
    failed = _combine_failed(failed, _expect_token(name, text, rules, number, "LONG_BLOCK", "long-block-comment"))
    return _combine_failed(failed, _expect_clean(name, text, rules, number))

def _expect_token(name: str, text: str, rules: set[str], number: int, token: str, rule: str) -> bool:
    """Report a missing comment rule. Args: name, text, rules, number, token, rule. Returns: bool failed."""
    if token not in text:
        return False
    if rule in rules:
        return False
    sys.stderr.write(f"{name}:{number}: {text!r} missed {rule}\n")
    return True

def _expect_clean(name: str, text: str, rules: set[str], number: int) -> bool:
    """Report a match on a clean or allowed line. Args: name, text, rules, number. Returns: bool failed."""
    if "CLEAN_" not in text and "ALLOW_" not in text:
        return False
    if not rules:
        return False
    sys.stderr.write(f"{name}:{number}: {text!r} matched {sorted(rules)}\n")
    return True

def _check_style(semgrep: list[str]) -> int:
    """Assert EXPECT and ALLOW markers on the style fixtures. Args: semgrep. Returns: int status."""
    statuses = [_check_style_file(name, semgrep) for name in STYLE_FIXTURES]
    return _first_failure(statuses)

def _check_style_file(name: str, semgrep: list[str]) -> int:
    """Check one style fixture. Args: name, semgrep. Returns: int status."""
    source = ROOT / "samples" / name
    code, findings = _scan_copy(semgrep, source)
    if code != 0:
        return code
    lines = source.read_text(encoding="utf-8").splitlines()
    expects, allows = _style_markers(lines)
    covered: dict[str, set[int]] = {}
    failed = _style_findings(name, findings, expects, covered)
    failed = _combine_failed(failed, _style_marks(name, expects, covered, False))
    failed = _combine_failed(failed, _style_marks(name, allows, covered, True))
    return _failed_status(failed)

def _scan_copy(semgrep: list[str], source: Path) -> tuple[int, list]:
    """Scan a temp copy so path excludes do not apply. Args: semgrep, source. Returns: tuple status findings."""
    with tempfile.TemporaryDirectory() as temporary:
        target = Path(temporary) / source.name
        shutil.copyfile(source, target)
        completed = _run_scan(semgrep, target, ("--json", "--quiet"), True)
        return _scan_result(completed)

def _scan_result(completed: subprocess.CompletedProcess[str]) -> tuple[int, list]:
    """Parse a JSON scan. Args: completed. Returns: tuple status findings."""
    if completed.returncode not in (0, 1):
        sys.stderr.write(completed.stderr)
        return (completed.returncode, [])
    parsed = json.loads(completed.stdout)["results"]
    return (0, parsed)

def _style_markers(lines: list[str]) -> tuple[dict[str, set[int]], dict[str, set[int]]]:
    """Collect EXPECT and ALLOW lines. Args: lines. Returns: tuple expects allows."""
    expects: dict[str, set[int]] = {}
    allows: dict[str, set[int]] = {}
    for number, text in enumerate(lines, start=1):
        _style_marker_line(text, expects, allows, number)
    return (expects, allows)

def _style_marker_line(text: str, expects: dict[str, set[int]], allows: dict[str, set[int]], number: int) -> None:
    """Record markers on one line. Args: text, expects, allows, number. Returns: none."""
    _add_markers(expects, re.findall(r"EXPECT:\s*([a-z0-9-]+)", text), number)
    _add_markers(allows, re.findall(r"ALLOW:\s*([a-z0-9-]+)", text), number)

def _add_markers(grouped: dict[str, set[int]], rules: list[str], number: int) -> None:
    """Add one line to each rule. Args: grouped, rules, number. Returns: none."""
    for rule in rules:
        grouped.setdefault(rule, set()).add(number)

def _style_findings(name: str, findings: list, expects: dict[str, set[int]], covered: dict[str, set[int]]) -> bool:
    """Check each finding. Args: name, findings, expects, covered. Returns: bool failed."""
    flags = [_style_finding(name, finding, expects, covered) for finding in findings]
    return _any_failed(flags)

def _style_finding(name: str, finding: dict, expects: dict[str, set[int]], covered: dict[str, set[int]]) -> bool:
    """Require ERROR and an EXPECT overlap. Args: name, finding, expects, covered. Returns: bool failed."""
    rule = finding["check_id"].rsplit(".", 1)[-1]
    start = finding["start"]["line"]
    end_line = finding["end"]["line"]
    failed = _style_severity(name, finding, rule)
    failed = _combine_failed(failed, _style_overlap(name, rule, start, end_line, expects))
    _cover_rule(covered, rule, start, end_line)
    return failed

def _style_severity(name: str, finding: dict, rule: str) -> bool:
    """Require ERROR on a style finding. Args: name, finding, rule. Returns: bool failed."""
    severity = finding["extra"]["severity"]
    if severity == "ERROR":
        return False
    sys.stderr.write(f"{name}:{finding['start']['line']}: {rule} severity {severity}\n")
    return True

def _style_overlap(name: str, rule: str, start: int, end_line: int, expects: dict[str, set[int]]) -> bool:
    """Fail when no EXPECT line sits in the span. Args: name, rule, start, end_line, expects. Returns: bool failed."""
    numbers = expects.get(rule, set())
    matched = [number for number in numbers if start <= number <= end_line]
    if matched:
        return False
    sys.stderr.write(f"{name}:{start}: unexpected {rule}\n")
    return True

def _cover_rule(covered: dict[str, set[int]], rule: str, start: int, end_line: int) -> None:
    """Record the lines a rule covered. Args: covered, rule, start, end_line. Returns: none."""
    lines = covered.setdefault(rule, set())
    for number in range(start, end_line + 1):
        lines.add(number)

def _style_marks(name: str, grouped: dict[str, set[int]], covered: dict[str, set[int]], forbid: bool) -> bool:
    """Check EXPECT lines, or ALLOW lines when forbid is set. Args: name, grouped, covered, forbid. Returns: bool failed."""
    flags = [
        _style_rule_lines(name, rule, numbers, covered.get(rule, set()), forbid)
        for rule, numbers in grouped.items()
    ]
    return _any_failed(flags)

def _style_rule_lines(name: str, rule: str, numbers: set[int], covered_lines: set[int], forbid: bool) -> bool:
    """Check marker lines for one rule. Args: name, rule, numbers, covered_lines, forbid. Returns: bool failed."""
    flags = [_style_mark_line(name, rule, number, covered_lines, forbid) for number in numbers]
    return _any_failed(flags)

def _style_mark_line(name: str, rule: str, number: int, covered_lines: set[int], forbid: bool) -> bool:
    """Report one marker miss or a suppressed hit. Args: name, rule, number, covered_lines, forbid. Returns: bool failed."""
    present = number in covered_lines
    if forbid and present:
        sys.stderr.write(f"{name}:{number}: allowed {rule} still matched\n")
        return True
    if (not forbid) and (not present):
        sys.stderr.write(f"{name}:{number}: missed {rule}\n")
        return True
    return False

def _any_failed(flags: list[bool]) -> bool:
    """True when any flag is set. Args: flags. Returns: bool failed."""
    failed = True in flags
    return failed

def _combine_failed(left: bool, right: bool) -> bool:
    """Combine two failure flags. Args: left, right. Returns: bool failed."""
    if left:
        return True
    return right

def _failed_status(failed: bool) -> int:
    """Turn a failure flag into an exit code. Args: failed. Returns: int status."""
    if failed:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
