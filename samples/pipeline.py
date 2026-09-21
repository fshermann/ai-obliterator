"""Run fix, then check, on a copy of the sample document."""

from __future__ import annotations

import difflib
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    before = ROOT / "samples" / "before.md"
    expected_path = ROOT / "samples" / "after.md"
    expected = expected_path.read_bytes()
    config = str(ROOT / "exodia.yml")
    tool = [sys.executable, str(ROOT / "run.py")]
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "sample.md"
        target.write_bytes(before.read_bytes())
        fix = subprocess.run([*tool, "fix", str(target), "--config", config], cwd=ROOT)
        if fix.returncode != 0:
            return fix.returncode
        check = subprocess.run([*tool, "check", str(target), "--config", config], cwd=ROOT)
        if check.returncode != 0:
            return check.returncode
        actual = target.read_bytes()
        if actual != expected:
            sys.stderr.writelines(
                difflib.unified_diff(
                    expected.decode("utf-8").splitlines(keepends=True),
                    actual.decode("utf-8").splitlines(keepends=True),
                    fromfile="samples/after.md",
                    tofile="pipeline output",
                )
            )
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
