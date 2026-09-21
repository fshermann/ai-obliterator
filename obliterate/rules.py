"""Built-in artifact rules and compilation of exodia.yml overrides."""

from __future__ import annotations

import re
from dataclasses import dataclass

from obliterate.errors import ObliterateError

_EMOJI_CHAR = (
    "\u2600-\u26FF"
    "\u2700-\u27BF"
    "\u2B50"
    "\u2B55"
    "\U0001F300-\U0001F5FF"
    "\U0001F600-\U0001F64F"
    "\U0001F680-\U0001F6FF"
    "\U0001F900-\U0001FAFF"
)
_EMOJI_BASE = f"[{_EMOJI_CHAR}]"
_EMOJI_PATTERN = (
    "(?:"
    "[#*0-9]\uFE0F?\u20E3"
    "|[\U0001F1E6-\U0001F1FF]{2}"
    f"|(?:{_EMOJI_BASE}\uFE0F?[\U0001F3FB-\U0001F3FF]?"
    f"(?:\u200D{_EMOJI_BASE}\uFE0F?[\U0001F3FB-\U0001F3FF]?)*)"
    ")"
)

_RULE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]*\Z")


@dataclass(frozen=True)
class Builtin:
    id: str
    pattern: str
    replacement: str
    enabled: bool


@dataclass(frozen=True)
class Rule:
    id: str
    pattern: re.Pattern[str]
    replacement: str
    literal: bool


@dataclass(frozen=True)
class RuleOverride:
    enabled: bool | None = None
    replacement: str | None = None


@dataclass(frozen=True)
class CustomRule:
    id: str
    pattern: str
    replacement: str
    enabled: bool = True


BUILTINS: tuple[Builtin, ...] = (
    Builtin("em-dash", "\u2014", " - ", True),
    Builtin("en-dash", "\u2013", "-", True),
    Builtin("horizontal-bar", "\u2015", "-", True),
    Builtin("minus-sign", "\u2212", "-", True),
    Builtin("ellipsis", "\u2026", "...", True),
    Builtin("smart-double-quotes", "[\u201c\u201d]", '"', True),
    Builtin("smart-single-quotes", "[\u2018\u2019]", "'", True),
    Builtin("nbsp", "\u00a0", " ", True),
    Builtin("zero-width", "[\u200b\u200c\u200d\ufeff]", "", True),
    Builtin("emoji", _EMOJI_PATTERN, "", True),
    Builtin("collapse-space", r"(?<=\S) {2,}", " ", False),
)

_BUILTIN_IDS = {item.id for item in BUILTINS}
_COLLAPSE_ID = "collapse-space"


def compile_rules(
    overrides: dict[str, RuleOverride],
    custom: list[CustomRule],
) -> list[Rule]:
    unknown = sorted(set(overrides) - _BUILTIN_IDS)
    if unknown:
        names = ", ".join(unknown)
        raise ObliterateError(f"unknown rule: {names}")

    seen: set[str] = set()
    for item in custom:
        if not _RULE_ID.match(item.id):
            raise ObliterateError(f"invalid custom rule id: {item.id}")
        if item.id in _BUILTIN_IDS or item.id in seen:
            raise ObliterateError(f"duplicate rule id: {item.id}")
        seen.add(item.id)

    compiled: list[Rule] = []
    collapse: Rule | None = None
    for builtin in BUILTINS:
        rule = _compile_builtin(builtin, overrides.get(builtin.id))
        if rule is None:
            continue
        if builtin.id == _COLLAPSE_ID:
            collapse = rule
        else:
            compiled.append(rule)

    for item in custom:
        if item.enabled:
            compiled.append(_compile_custom(item))

    if collapse is not None:
        compiled.append(collapse)
    return compiled


def _compile_builtin(builtin: Builtin, override: RuleOverride | None) -> Rule | None:
    enabled = builtin.enabled
    replacement = builtin.replacement
    if override is not None:
        if override.enabled is not None:
            enabled = override.enabled
        if override.replacement is not None:
            replacement = override.replacement
    if not enabled:
        return None
    return Rule(
        id=builtin.id,
        pattern=_compile_pattern(builtin.id, builtin.pattern),
        replacement=replacement,
        literal=True,
    )


def _compile_custom(item: CustomRule) -> Rule:
    return Rule(
        id=item.id,
        pattern=_compile_pattern(item.id, item.pattern),
        replacement=item.replacement,
        literal=False,
    )


def _compile_pattern(rule_id: str, pattern: str) -> re.Pattern[str]:
    if pattern == "":
        raise ObliterateError(f"rule {rule_id}: pattern must not be empty")
    try:
        compiled = re.compile(pattern)
    except re.error as exc:
        raise ObliterateError(f"rule {rule_id}: invalid pattern: {exc}") from exc
    if compiled.match(""):
        raise ObliterateError(f"rule {rule_id}: pattern must not match empty text")
    return compiled
