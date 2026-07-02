"""ai-obliterator CLI entry point."""

from __future__ import annotations

import argparse
import sys
from typing import Callable

from commands import foo, bar


COMMANDS: dict[str, Callable[[], None]] = {
    "foo": foo.run,
    "bar": bar.run,
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ai-obliterator",
        description="A super basic CLI tool.",
    )
    parser.add_argument(
        "--foo", "-f",
        action="store_true",
        help="Print foo.",
    )
    parser.add_argument(
        "--bar", "-b",
        action="store_true",
        help="Print bar.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    selected = [name for name, flag in (("foo", args.foo), ("bar", args.bar)) if flag]

    if not selected:
        parser.print_help(sys.stderr)
        return 1

    for name in selected:
        COMMANDS[name]()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
