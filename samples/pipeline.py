"""Copy the fixtures, autofix them with Semgrep, then check the result."""

from __future__ import annotations

import difflib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "semgrep" / "ai-artifacts.yml"
FIXTURES = ("before.py", "before.js")


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
    return 0


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


def _snapshot(directory: Path) -> dict[str, bytes]:
    return {path.name: path.read_bytes() for path in sorted(directory.iterdir())}


if __name__ == "__main__":
    raise SystemExit(main())
