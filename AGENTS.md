# AGENTS.md

Notes for AI coding agents working in this repository.

## Project

`ai-obliterator` strips AI writing artifacts (em dashes, smart quotes, emoji,
and similar characters) from text files. Rules live in `exodia.yml`. `check`
is the pipeline gate. `fix` rewrites files.

## Environment

- Windows, PowerShell 5.1.
- Python 3.12, virtualenv at `.venv/`.
- Always invoke Python and tools via the venv, never system Python:
  - `.venv\Scripts\python.exe`
  - `.venv\Scripts\pip.exe`
  - `.venv\Scripts\pyinstaller.exe`
  - `.venv\Scripts\ai-obliterator.exe` (installed console script)

## Layout

```
run.py                 # entry point, calls cli.main
cli/__init__.py        # argparse subcommands
commands/              # one file per command, each exposes run(args) -> int
  __init__.py
  check.py
  fix.py
obliterate/            # config, rule table, scanner
  config.py
  rules.py
  scan.py
exodia.yml             # rule config
samples/               # fixture and sample pipeline
.github/workflows/obliterator.yml
pyproject.toml
requirements-dev.txt
README.md
.gitignore
```

Keep `cli/` as a package directory. An editable install resolves the console
script from that package. A single `cli.py` file breaks `pip install -e .`
on this setup.

## Conventions

- Each command module under `commands/` exposes `def run(args) -> int`.
- To add a command: create the file, then register it in the `COMMANDS` dict
  in `cli/__init__.py` and add a subparser in `build_parser()`.
- Built-in artifact rules live in `obliterate/rules.py`. Editable overrides and
  custom patterns live in `exodia.yml`.
- No comments in code unless the user explicitly asks for them.
- Prefer the standard library. PyYAML is the runtime dependency for `exodia.yml`.
  The only dev dependency is PyInstaller.
- Don't add lint/format/test config proactively. The user has not asked for it.

## Build

```sh
.venv\Scripts\pyinstaller.exe --clean pyinstaller.spec
# output: dist/ai-obliterator.exe
```

A PyInstaller spec should collect both `commands` and `obliterate` so the
dispatch targets and the rule engine survive freezing.

## Pipeline

`.github/workflows/obliterator.yml` installs the package, runs
`ai-obliterator check .`, then runs `samples/pipeline.py`.

## Things to avoid

- Don't run `pyinstaller` against `run.py` directly with ad-hoc flags; use the
  spec file so hiddenimports stay in sync.
- Don't commit `.venv/`, `build/`, or `dist/`. `*.spec` is gitignored.
- Don't use `Set-Location` (cd) in bash commands; use the `workdir` parameter.
- Don't use `&&` to chain PowerShell commands; use `; if ($?) { ... }` instead.
