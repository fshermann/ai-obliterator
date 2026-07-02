# ai-obliterator

A super basic Python CLI tool.

## Usage

```sh
python run.py --foo   # prints: foo
python run.py -f      # short form
python run.py --bar   # prints: bar
python run.py -b      # short form
python run.py -f -b   # prints: foo then bar
python run.py --help  # show help
```

Running with no flags prints help to stderr and exits with code 1.

## Project layout

```
ai-obliterator/
├── run.py              # entry point
├── cli.py              # argparse parser + command dispatch
├── commands/
│   ├── __init__.py
│   ├── foo.py          # --foo / -f
│   └── bar.py          # --bar / -b
├── pyproject.toml      # project metadata + build config
├── requirements-dev.txt
└── .gitignore
```

### Adding a new command

1. Create `commands/<name>.py` exposing `def run() -> None: ...`.
2. Register it in `COMMANDS` in `cli.py` and add an `argparse` flag.

## Development

Requires Python 3.10+.

```sh
python run.py --help
```

## Building an executable

The project ships with a PyInstaller spec. From the project root:

```sh
pip install -r requirements-dev.txt
pyinstaller --clean pyinstaller.spec
```

The standalone binary is produced at `dist/ai-obliterator.exe` (Windows) or
`dist/ai-obliterator` (Linux/macOS).

To rebuild from scratch:

```sh
rm -rf build dist
pyinstaller --clean pyinstaller.spec
```
