"""check command: report AI artifacts and exit 1 when any remain."""

from __future__ import annotations

import argparse

from obliterate.scan import execute


def run(args: argparse.Namespace) -> int:
    return execute(args, write=False)
