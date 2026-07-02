# AGENTS.md

Notes for AI coding agents working in this repository.

## Project

`ai-obliterator` — a tiny Python CLI demo. Two flags (`--foo`/`-f`, `--bar`/`-b`),
each handled by a separate module under `commands/`.

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
cli/__init__.py        # argparse parser + dispatch table (COMMANDS dict)
commands/              # one file per command, each exposes run()
    __init__.py
    foo.py
    bar.py
pyproject.toml         # project metadata; [project.scripts] -> ai-obliterator
requirements-dev.txt   # pyinstaller
pyinstaller.spec       # one-file build config
README.md
.gitignore
```

The package layout is intentional: `cli/` is a directory (not `cli.py`) so the
editable install and the `ai-obliterator` console script resolve correctly.
**Do not** flatten `cli/` back into a single `cli.py` file — it breaks
`pip install -e .` on this setup.

## Conventions

- Each command module under `commands/` exposes a single `def run() -> None: ...`.
- To add a command: create the file, then register it in the `COMMANDS` dict
  in `cli/__init__.py` and add the `argparse` flag in `build_parser()`.
- No comments in code unless the user explicitly asks for them.
- Prefer stdlib only. The only dev dep is PyInstaller.
- Don't add lint/format/test config proactively — the user has not asked for it.

## Build

```sh
.venv\Scripts\pyinstaller.exe --clean pyinstaller.spec
# output: dist/ai-obliterator.exe
```

`pyinstaller.spec` uses `collect_submodules('commands')` so the dispatch
targets survive freezing — keep that if you change the commands package.

## Things to avoid

- Don't run `pyinstaller` against `run.py` directly with ad-hoc flags; use the
  spec file so hiddenimports stay in sync.
- Don't commit `.venv/`, `build/`, `dist/`, `*.spec` are already in `.gitignore`
  for some entries — check `.gitignore` before adding new artifacts.
- Don't use `Set-Location` (cd) in bash commands; use the `workdir` parameter.
- Don't use `&&` to chain PowerShell commands; use `; if ($?) { ... }` instead.
