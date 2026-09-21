# ai-obliterator

Strip AI writing artifacts from text files. `check` reports them and fails the
process. `fix` rewrites files in place. Rules live in `exodia.yml`.

## Usage

```sh
ai-obliterator check .
ai-obliterator fix .
ai-obliterator check path/to/file.md
ai-obliterator fix - < draft.md
```

With no path, the command scans the current directory. `check` prints
`file:line:column: rule: snippet` and exits 1 when it finds anything. `fix`
prints the paths it changed and exits 0. Exit 2 means a bad config, a missing
path, or an unreadable file.

`--config` / `-c` selects a config file. Without it, the tool walks upward from
the working directory for `exodia.yml`. `--format json` prints a single JSON
object. `fix -` always writes the rewritten text to stdout.

## Rules

Built-in rules ship with the tool. `exodia.yml` turns them off or replaces
their replacement text. `custom` adds Python regular expressions; those
replacements can use backreferences. Built-in replacements stay literal.

| id | match | default replacement | default |
|---|---|---|---|
| `em-dash` | U+2014 | ` - ` | on |
| `en-dash` | U+2013 | `-` | on |
| `horizontal-bar` | U+2015 | `-` | on |
| `minus-sign` | U+2212 | `-` | on |
| `ellipsis` | U+2026 | `...` | on |
| `smart-double-quotes` | U+201C U+201D | `"` | on |
| `smart-single-quotes` | U+2018 U+2019 | `'` | on |
| `nbsp` | U+00A0 | space | on |
| `zero-width` | U+200B U+200C U+200D U+FEFF | empty | on |
| `emoji` | emoji and pictographs, including ZWJ sequences | empty | on |
| `collapse-space` | repeated spaces after a non-space | one space | off |

Dashes and punctuation run first, then invisible characters and emoji, then
`custom` rules. `collapse-space` runs last when you enable it. Line and column
refer to the original file.

Directory scans use `include` and `exclude`. An explicit file path is scanned
either way. The loaded config file is skipped during directory scans. `.git`,
virtualenvs, `__pycache__`, `dist`, `build`, and `*.egg-info` are always
skipped. Binary files and files that are not UTF-8 are skipped.

## Sample pipeline

`.github/workflows/obliterator.yml` installs the package, runs
`ai-obliterator check .`, then runs the sample fixer:

```sh
python samples/pipeline.py
```

That script copies `samples/before.md`, runs `fix`, runs `check`, and compares
the result with `samples/after.md`. `samples/` is excluded from the repository
check because the input file still contains artifacts.

## Project layout

```
run.py
cli/__init__.py
commands/check.py
commands/fix.py
obliterate/
exodia.yml
samples/pipeline.py
.github/workflows/obliterator.yml
```

### Adding a command

1. Create `commands/<name>.py` exposing `def run(args) -> int`.
2. Register it in `COMMANDS` in `cli/__init__.py` and add a subparser.

## Development

Requires Python 3.10+.

```sh
python -m pip install -e .
ai-obliterator check .
python samples/pipeline.py
```

## Building an executable

```sh
pip install -r requirements-dev.txt
pyinstaller --clean pyinstaller.spec
```

The standalone binary is produced at `dist/ai-obliterator.exe` (Windows) or
`dist/ai-obliterator` (Linux/macOS). Collect the `commands` and `obliterate`
packages so the frozen binary keeps the dispatch targets and the rule engine.
