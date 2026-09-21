# AGENTS.md

Notes for AI coding agents working in this repository.

## Project

`ai-obliterator` is a Semgrep ruleset. It strips AI writing artifacts from
Python and JavaScript: dashes, smart quotes, ellipsis, non-breaking spaces,
zero-width characters, emoji, and one custom phrase. The rules live in
`semgrep/ai-artifacts.yml`.

## Environment

- Windows, PowerShell 5.1, or the Linux CI image.
- Python 3.12. Install Semgrep with `python -m pip install -e .`
  (pinned in `pyproject.toml`).
- Invoke Semgrep as `semgrep` or `python -m semgrep`.

## Layout

```
semgrep/ai-artifacts.yml          # the rules
samples/before.py                 # dirty fixture, excluded from the repo scan
samples/before.js
samples/after.py                  # expected autofix output
samples/after.js
samples/pipeline.py               # autofix, check, compare
.github/workflows/obliterator.yml
pyproject.toml
README.md
```

## Conventions

- Add or change a substitution in `semgrep/ai-artifacts.yml`. Keep
  `languages: [generic]` and the shared `paths` anchor so Python and
  JavaScript stay on the same rules.
- A fix that is only spaces will be trimmed by Semgrep. Pad it with U+2060
  and let `fix-padding` remove the padding on the next autofix pass.
- Run autofix twice, or until the files stop changing, then
  `semgrep scan --config semgrep/ai-artifacts.yml --error --metrics=off .`
- No comments in code unless the user explicitly asks for them.
- Don't add lint, format, or test config proactively.

## Pipeline

`.github/workflows/obliterator.yml` installs the project, scans the
repository, then runs `samples/pipeline.py`.

## Things to avoid

- Don't replace this ruleset with a hand-rolled scanner.
- Don't scan `samples/before.py` or `samples/before.js` in the repository
  check. Those fixtures are excluded because they still contain artifacts.
- Don't commit `.venv/`, `build/`, or `dist/`.
- Don't use `Set-Location` (cd) in bash commands; use the `workdir` parameter.
- Don't use `&&` to chain PowerShell commands; use `; if ($?) { ... }` instead.
