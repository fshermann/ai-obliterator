# ai-obliterator

Semgrep rules for Python, JavaScript, TypeScript, Terraform, and C++. The
artifact rules in `semgrep/ai-artifacts.yml` strip AI writing: dashes, smart
quotes, ellipsis, non-breaking spaces, zero-width characters, emoji, and a
list of AI phrases. The other files under `semgrep/` are an opinionated Python
style suite. Point Semgrep at the `semgrep/` directory so both sets run.

Errors fail `semgrep scan --severity ERROR --error`. Warnings are reported
with `--severity WARNING` and do not fail that check. `fix` is
`semgrep scan --autofix`, run until the files stop changing. A comment longer
than three lines is also an error unless it contains `obliterator-allow`.

## Usage

```sh
python -m pip install -e .
semgrep scan --config semgrep --severity WARNING --metrics=off .
semgrep scan --config semgrep --severity ERROR --error --metrics=off .
semgrep scan --config semgrep --autofix --metrics=off .
semgrep scan --config semgrep --autofix --metrics=off .
```

The second autofix removes U+2060 word joiners. Semgrep trims spaces from a
fix, so the em dash and non-breaking space replacements are padded with word
joiners and a follow-up rule deletes that padding. It also finishes emoji
sequences whose joiners were removed by the zero-width rule.

`--error` exits 1 when a reported finding remains. Limit it with
`--severity ERROR` so wording warnings stay visible without failing the check.
A bad config or an unreadable target is a Semgrep error exit.

## Rules

The rules use Semgrep generic mode, limited to Python, JavaScript, TypeScript,
Terraform, and C++ paths, so the same text replacement applies in code, strings,
and comments. Terraform is included as `.tf`, `.tfvars`, and `.hcl`. TypeScript
is included as `.ts`, `.tsx`, `.mts`, and `.cts`. C++ is included as `.cpp`,
`.cc`, `.cxx`, `.h`, `.hpp`, `.hh`, and `.hxx`.

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
| `no-ai-phrase` | `delve into` | `look at` |
| `ai-phrase` | blocked AI phrases below | report only |
| `ai-wording` | warning phrases below | report only |
| `fix-padding` | U+2060 | empty |
| `long-line-comment` | 4 or more consecutive `#` or `//` lines | report only |
| `long-block-comment` | a docstring or block comment of 4 or more lines | report only |

`ai-phrase` is an error. `ai-wording` is a warning. Matches are case-insensitive.
`holistic` and `multifaceted` are errors. `delve into` is rewritten to `look at`
and is not also reported as a bare `delve`. The other phrases are reported and
left in place.

Errors: delve, delve into, tapestry, rich tapestry, testament to, a testament to,
multifaceted, paradigm shift, ever-evolving, cutting-edge, state-of-the-art,
game-changer, groundbreaking, unprecedented, unparalleled, transformative,
revolutionary, in today's fast-paced world, navigate the complexities,
navigating the landscape, a beacon of, at the forefront of, plays a pivotal role,
pivotal, holistic, seamless, seamlessly.

Warnings: robust, leverage, leveraging, foster, garner, plethora, myriad,
comprehensive, underscore, underscores, showcase, elevate, unlock, unleash,
embark, journey, realm, landscape, intricate, intricacies, meticulous, enduring,
enhance, interplay, noteworthy, harness, cornerstone, hallmark, nexus, zeitgeist,
pinnacle, frontier, trajectory, synergy, empower, streamline, impactful,
actionable, scalable, nuanced, dynamic, innovative, facilitate, utilize,
commence, endeavor, profound, remarkable, exceptional, paramount, renowned,
spearhead, catalyze, propel, amplify, champion, it's important to note that,
it is important to note that, it's worth noting that, it is worth noting that,
it's worth considering, it is worth considering, in conclusion, overall,
ultimately, furthermore, moreover, additionally, that being said, with that in
mind, in today's, in the ever-evolving, as we navigate, when it comes to, at the
end of the day, building on this, taking this a step further, this highlights,
this underscores, this demonstrates, this serves as, a key consideration is, one
of the most important, there are several factors, there are a number of, on the
one hand, on the other hand, not only ... but also.

`Overall,`, `Ultimately,`, `Furthermore,`, `Moreover,`, and `Additionally,` keep
the comma. `not only … but also` allows a short gap between the two halves.
`In the ever-evolving` warns, and `ever-evolving` inside it is still an error.

The `samples/before.*` fixtures are excluded so the repository check stays
clean. Every other matching source file is included.

## Long comments

`long-line-comment` and `long-block-comment` are errors. Three lines are
allowed. Four or more fail `semgrep scan --severity ERROR --error`.

A single-line run is consecutive lines whose first non-space characters are
`#` or `//`. A blank line starts a new run. Those are the single-line comment
syntaxes of Python, JavaScript, TypeScript, Terraform, and C++.

A block comment is a `/* */` comment whose `/*` starts the line, or a `"""` /
`'''` block, including a docstring, whose opening quotes start the line.
An optional Python string prefix such as `r` may sit in front of the quotes.
A triple-quoted string that shares its opening line with other code is left
alone. Inside the block, three lines are allowed and the fourth line fails.

Put `obliterator-allow` inside the comment to keep that comment. The token
does not suppress other rules.

```python
# obliterator-allow
# kept on purpose
# across four
# lines
```

```python
"""obliterator-allow
Kept on purpose.
This docstring is
four lines long.
"""
```

```javascript
// obliterator-allow
// kept
// on
// purpose
```

```javascript
/* obliterator-allow
   kept on purpose
   across four
   lines
*/
```

## Python style

Style rules are Python only, except `long-file`, which counts lines in the
same source extensions as the artifact rules. Every style rule is an error.
`obliterator-allow` inside the matched text suppresses that finding. A comment
on the previous line does not count. For a function, put it on the `def` line
or in the body. For `try`, put it on the `try` line or inside the block. The
short-assignment check is a line regex, so a trailing comment on that line
counts.

### Docstrings

Every function and method needs a docstring of 1 to 3 lines with a short
description, an `Args:` mention, and a `Returns:` mention. Use `Args: none`
or `Returns: none` when there are none. A good form is one line:

```python
def score_visit(patient):
    """Score the visit. Args: patient. Returns: int score."""
    return 1
```

`Args:` and `Returns:` are case-sensitive. A missing docstring, a missing
`Args:`, a missing `Returns:`, or a description with neither mention is an
error. Functions named `test_*` are exempt. A `"""` / `'''` block of 4 or
more lines is already `long-block-comment`. Do not lengthen the docstring to
escape that rule.

### Names

`short-name` errors on function, class, and variable names shorter than 4
characters. `short-token` errors on an underscore-separated token of 1 or 2
characters (`calc_sc`, `load_by_id`). Single-letter loop targets are short
names (`for i in patients`). The rules do not guess English abbreviations.

Allowed:

- `self` is 4 characters, so the length rule does not flag it
- `cls` and `id`
- `_` and names that are only underscores
- `_id` and `__id`
- token segments `id` and `cls` (`patient_id`, `model_cls`)

`args` and `kwargs` pass because they are longer than 3 characters. Star
names are checked without the stars (`*xs` checks `xs`). Attribute
assignments (`self.x = 1`) and bare imports are not flagged. Import aliases
are flagged.

### Structure

| id | rule |
|---|---|
| `nested-block` | an `if`, `for`, `while`, `with`, or `try` directly inside another of those |
| `long-chain` | an attribute or call chain of 5 or more links (`a.b.c.d.e`) |
| `multiple-decorators` | more than one decorator on a function or method |
| `multiple-classes` | more than one `class` statement in a file |
| `inherits` | `class Child(Parent)` unless every base is allowlisted |
| `long-file` | more than 500 lines |

The function body is nesting level 0. A nested `def` resets to level 0.
Comprehensions do not count. Chains of 4 links are allowed (`a.b.c.d`). A
call in the middle is still one link (`a.b().c.d.e`). `@property`,
`@staticmethod`, and `@classmethod` count toward the decorator limit. One
decorator is allowed. Nested classes count toward `multiple-classes`.

Inheritance bases that are allowed, exactly: `Exception`, `BaseException`,
and `Enum`, plus a dotted prefix such as `enum.Enum` or `builtins.Exception`.
`ValueError`, `IntEnum`, `Protocol`, and `NamedTuple` are errors.
`obliterator-allow` is the escape hatch.

### Tests, duplication, and typing

`repeated-literal-asserts` flags a `test_*` function with 3 or more adjacent
`assert func(literal) == literal` checks. `sibling-literal-tests` flags 3 or
more consecutive `test_*` functions whose whole body is that one assert.
Ordinary tests that pass names, helpers that are not named `test_*`, and a
single assert are not flagged.

`wrapper-call` flags a function whose body is only a call, or only
`return` of a call, with or without a docstring. `same-body` flags two
adjacent functions whose body is one identical statement, or a docstring plus
one identical statement. Identical `return 1` is flagged. A bare
`return score(patient)` is flagged. A returned call after a docstring is not
compared, and an expression statement such as `save(patient)` is not compared.

`builtin-generic` is a short denylist. Use the builtin or the `|` union:

| import | use |
|---|---|
| `typing.List` | `list` |
| `typing.Dict` | `dict` |
| `typing.Set` | `set` |
| `typing.Tuple` | `tuple` |
| `typing.FrozenSet` | `frozenset` |
| `typing.Type` | `type` |
| `typing.Optional` | `X \| None` |
| `typing.Union` | `A \| B` |

The rule matches `from typing import Name`, `from typing import Name as Alias`,
and `typing.Name`. `Any`, `Protocol`, `NamedTuple`, and `TypeVar` are not on
the list. `import typing as t` followed by `t.List` is not matched.

### Defensive checks

`redundant-type-check` flags `isinstance` and `type(...)` comparisons (`is`,
`==`, `is not`, `!=`) of a name already annotated as that exact type, on a
parameter or an annotated assignment. A union such as `Patient | None` and a
quoted annotation are not flagged.

`defensive-handler` flags every `try` / `except`, including a bare `except`
and `except Exception`. A `try` / `finally` with no `except` is not flagged.
`obliterator-allow` is the escape hatch.

### Gaps

These checks are not shipped. A noisy approximation would fail ordinary code,
and Semgrep cannot see them soundly.

- Functions called only once. Semgrep has no occurrence count. A pattern that
  sees one call also matches a function called many times. Intra-file and
  cross-file are both out.
- Classes longer than 500 lines. There is no span-length condition. An indent
  regex miscounts strings, comments, and mixed indent. File length is shipped
  because a file-anchored regex can count lines.
- Parameterized tests beyond the two shapes above: asserts that are not `==`,
  calls with more than one argument, non-adjacent asserts, sibling tests
  whose bodies are longer than one assert, and f-strings. A looser pattern
  flags ordinary tests.
- YAGNI and the rest of DRY: speculative unused code, similar but not
  identical bodies, cross-file duplication, and "this abstraction is
  premature." There is no vague wording regex.
- Nesting in an `else` or `elif`, and an `if` that appears only in a `for` or
  `while` `else` clause. Semgrep stores `elif` as `else` plus `if`, so that
  pattern flags every `elif` chain. Nesting in the body, in `except`, and in
  `finally` is flagged.
- Inheritance is an exact allowlist, not "any exception type."
- The typing denylist is only the aliases in the table. Libraries such as
  numpy, pandas, and requests are judgment calls and are not banned.
- Chains with more than one level of nested parentheses in a call argument,
  or a subscript in the chain (`a.b[0].c.d.e`), may be missed. The chain rule
  is Python only.
- Decorators deeper than `a.b.c(...)` may be missed.
- String annotations are not compared for redundant type checks.
- `long-file` is suppressed when `obliterator-allow` appears in the first 501
  lines, because that is the matched span.

## Sample pipeline

`.github/workflows/obliterator.yml` installs this project, scans the
repository, then runs:

```sh
python samples/pipeline.py
```

That script copies the fixtures, autofixes them, checks them, and compares the
result with `samples/after.py`, `samples/after.js`, `samples/after.ts`,
`samples/after.tf`, and `samples/after.cpp`. It also checks
`samples/comments.py`, `samples/comments.js`, `samples/comments.ts`,
`samples/comments.tf`, and `samples/comments.cpp` for long runs, three-line
runs, and `obliterator-allow`. `samples/style.py` and `samples/long_file.py`
hold intentional style violations and `obliterator-allow` examples. Those
fixtures are excluded from the repository scan, same as `samples/phrases.py`.

## Project layout

```
semgrep/ai-artifacts.yml
semgrep/names.yml
semgrep/docstrings.yml
semgrep/practice.yml
semgrep/structure.yml
samples/pipeline.py
samples/style.py
samples/long_file.py
.github/workflows/obliterator.yml
pyproject.toml
```
