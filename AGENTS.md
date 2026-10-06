# AGENTS.md

Notes for AI coding agents working in this repository.

## Project

`ai-obliterator` is a Semgrep ruleset. It strips AI writing artifacts from
Python, JavaScript, TypeScript, Terraform, and C++: dashes, smart quotes, ellipsis, non-breaking spaces,
zero-width characters, emoji, and a list of AI phrases. Separate files under
`semgrep/` add an opinionated Python style suite. Errors and warnings are
separate severities. Artifact rules live in `semgrep/ai-artifacts.yml`. Scan
the `semgrep/` directory so every file is included.

## Environment

- Windows, PowerShell 5.1, or the Linux CI image.
- Python 3.12. Install Semgrep with `python -m pip install -e .`
  (pinned in `pyproject.toml`).
- Invoke the `semgrep` binary (`bin/semgrep` or `Scripts/semgrep.exe`). `python -m semgrep` is deprecated and exits 2.

## Layout

```
semgrep/ai-artifacts.yml          # character and phrase rules
semgrep/names.yml                 # short names and short tokens
semgrep/docstrings.yml            # docstring shape
semgrep/practice.yml              # tests, wrappers, typing, handlers
semgrep/structure.yml             # nesting, chains, classes, file length
samples/before.py                 # dirty fixtures, excluded from the repo scan
samples/before.js
samples/before.ts
samples/before.tf
samples/before.cpp
samples/after.py                  # expected autofix output
samples/after.js
samples/after.ts
samples/after.tf
samples/after.cpp
samples/phrases.py                # phrase fixtures, excluded from the repo scan
samples/comments.py               # long-comment fixtures, excluded from the repo scan
samples/comments.js
samples/comments.ts
samples/comments.tf
samples/comments.cpp
samples/style.py                  # style fixtures, excluded from the repo scan
samples/long_file.py              # 501-line fixture, excluded from the repo scan
samples/pipeline.py               # autofix, check, compare
.github/workflows/obliterator.yml
pyproject.toml
README.md
```

## Conventions

- Add or change an artifact substitution in `semgrep/ai-artifacts.yml`. Keep
  `languages: [generic]` and the shared `paths` anchor so Python, JavaScript,
  TypeScript, Terraform, and C++ stay on the same rules.
- Add a style rule as its own file under `semgrep/`, or extend an existing
  style file. Do not fold style checks into the artifact rules.
- A fix that is only spaces will be trimmed by Semgrep. Pad it with U+2060
  and let `fix-padding` remove the padding on the next autofix pass.
- Run autofix twice, or until the files stop changing, then
  `semgrep scan --config semgrep --severity ERROR --error --metrics=off .`
- Phrase matches are case-insensitive. `delve into` rewrites to `look at`.
  The other phrases are reported and not rewritten. `holistic` and
  `multifaceted` are errors.
- No comments in code unless the user explicitly asks for them.
- Don't add lint, format, or test config proactively.

## Pipeline

`.github/workflows/obliterator.yml` installs the project, scans the
repository, then runs `samples/pipeline.py`.

## Things to avoid

- Don't replace this ruleset with a hand-rolled scanner.
- Don't scan the `samples/before.*` fixtures, `samples/phrases.py`,
  `samples/comments.*`, `samples/style.py`, or `samples/long_file.py` in the
  repository check. They are excluded because they still contain artifacts.
  `obliterator-allow` inside a comment keeps a run longer than three lines,
  and the same token inside a matched finding suppresses that style finding.
- Don't commit `.venv/`, `build/`, or `dist/`.
- Don't use `Set-Location` (cd) in bash commands; use the `workdir` parameter.
- Don't use `&&` to chain PowerShell commands; use `; if ($?) { ... }` instead.
