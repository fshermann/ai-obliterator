"""ai-obliterator CLI entry point."""

from __future__ import annotations

import argparse
import sys
from typing import Callable

from commands import check, fix
from obliterate.errors import ObliterateError


COMMANDS: dict[str, Callable[[argparse.Namespace], int]] = {
    "check": check.run,
    "fix": fix.run,
}


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--config",
        "-c",
        help="Path to exodia.yml. Defaults to the nearest exodia.yml.",
    )
    common.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format. Defaults to text.",
    )
    parser = argparse.ArgumentParser(
        prog="ai-obliterator",
        description="Strip AI writing artifacts from text files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "exit codes:\n"
            "  0  check found nothing, or fix finished\n"
            "  1  check found artifacts\n"
            "  2  usage, config, or file error\n"
            "\n"
            "examples:\n"
            "  ai-obliterator check .\n"
            "  ai-obliterator fix .\n"
            "  ai-obliterator fix - < draft.md"
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name, help_text in (
        ("check", "Report artifacts and exit 1 if any are found."),
        ("fix", "Rewrite files in place."),
    ):
        subparser = subparsers.add_parser(name, parents=[common], help=help_text)
        subparser.add_argument(
            "paths",
            nargs="*",
            metavar="PATH",
            help="Files or directories to scan. Defaults to the current directory. Use - for stdin.",
        )
    return parser


def main(argv: list[str] | None = None) -> int:
    _configure_stdio()
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return COMMANDS[args.command](args)
    except ObliterateError as exc:
        print(f"ai-obliterator: {exc}", file=sys.stderr)
        return 2


def _configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(errors="backslashreplace")
        except (OSError, ValueError):
            continue


if __name__ == "__main__":
    raise SystemExit(main())
