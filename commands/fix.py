"""fix command: rewrite files so enabled rules no longer match."""

from __future__ import annotations

import argparse

from obliterate.scan import execute


def run(args: argparse.Namespace) -> int:
    return execute(args, write=True)
