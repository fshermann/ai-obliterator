# ai-obliterator

Semgrep rules that strip AI writing artifacts from Python, JavaScript,
TypeScript, and Terraform. One ruleset, `semgrep/ai-artifacts.yml`, covers
all of them. `check` is
`semgrep scan --error`. `fix` is `semgrep scan --autofix`, run until the files
stop changing.

## Usage

```sh
python -m pip install -e .
semgrep scan --config semgrep/ai-artifacts.yml --error --metrics=off .
semgrep scan --config semgrep/ai-artifacts.yml --autofix --metrics=off .
semgrep scan --config semgrep/ai-artifacts.yml --autofix --metrics=off .
```

The second autofix removes U+2060 word joiners. Semgrep trims spaces from a
fix, so the em dash and non-breaking space replacements are padded with word
joiners and a follow-up rule deletes that padding. It also finishes emoji
sequences whose joiners were removed by the zero-width rule.

Semgrep exits 1 when `--error` finds a match. A bad config or an unreadable
target is a Semgrep error exit.

## Rules

The rules use Semgrep generic mode, limited to Python, JavaScript, TypeScript,
and Terraform paths, so the same text replacement applies in code, strings,
and comments. Terraform is included as `.tf`, `.tfvars`, and `.hcl`. TypeScript
is included as `.ts`, `.tsx`, `.mts`, and `.cts`.

| id | match | replacement |
|---|---|---|
| `em-dash` | U+2014 | spaced hyphen |
| `en-dash` | U+2013 | `-` |
| `horizontal-bar` | U+2015 | `-` |
| `minus-sign` | U+2212 | `-` |
| `ellipsis` | U+2026 | `...` |
| `smart-double-quotes` | U+201C U+201D | `"` |
| `smart-single-quotes` | U+2018 U+2019 | `'` |
| `nbsp` | U+00A0 | space |
| `zero-width` | U+200B U+200C U+200D U+FEFF | empty |
| `emoji` | emoji and pictographs, including ZWJ sequences | empty |
| `no-ai-phrase` | `delve\s+into` | `look at` |
| `fix-padding` | U+2060 | empty |

The `samples/before.*` fixtures are excluded so the repository check stays
clean. Every other matching source file is included.

## Sample pipeline

`.github/workflows/obliterator.yml` installs this project, scans the
repository, then runs:

```sh
python samples/pipeline.py
```

That script copies the fixtures, autofixes them, checks them, and compares the
result with `samples/after.py`, `samples/after.js`, `samples/after.ts`, and
`samples/after.tf`.

## Project layout

```
semgrep/ai-artifacts.yml
samples/pipeline.py
.github/workflows/obliterator.yml
pyproject.toml
```
