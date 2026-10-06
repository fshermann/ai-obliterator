import os
import sys as io  # EXPECT: short-name
from typing import Any
from typing import List  # EXPECT: builtin-generic
import typing

hint: typing.Dict  # EXPECT: builtin-generic


def score_visit(patient):
    """Score the visit. Args: patient. Returns: int score."""
    total = 1
    return total


def show_assignment_text():
    """Show an assignment inside text. Args: none. Returns: str text."""
    return """
    x = 1
    """


def short_function():
    """Return a short name. Args: none. Returns: int."""
    def ab():  # EXPECT: short-name
        """Return one. Args: none. Returns: int."""
        return 11
    return ab()


def zz():  # obliterator-allow ALLOW: short-name
    """Keep the short name. Args: none. Returns: int."""
    return 12


def calc_sc(patient):  # EXPECT: short-token
    """Score the visit. Args: patient. Returns: int score."""
    return 13


def load_patient_id(patient):
    """Load the visit. Args: patient. Returns: int score."""
    return 14


def store_names():
    """Store a few names. Args: none. Returns: none."""
    x = 1  # EXPECT: short-name
    kept = x
    id = 2
    _id = 3
    cls = 4
    _ = 5
    y = 6  # obliterator-allow ALLOW: short-name
    kept = y


def walk_patients(patients):
    """Walk the rows. Args: patients. Returns: none."""
    for i in patients:  # EXPECT: short-name
        report_patient(i)
    for _ in patients:
        report_patient(patients)
    for index in patients:
        report_patient(index)
    for a, patient in patients:  # EXPECT: short-name
        report_patient(patient)


def keyword_only(*, n):  # EXPECT: short-name
    """Score one flag. Args: n. Returns: int."""
    return 15


def accept_star(*xs):  # EXPECT: short-name
    """Pass the rest. Args: xs. Returns: tuple values."""
    return xs


def open_handle(path):
    """Open a file. Args: path. Returns: none."""
    with open(path) as f:  # EXPECT: short-name
        report_work()


def missing_doc(patient):  # EXPECT: missing-docstring
    return 16


def description_only(patient):  # EXPECT: docstring-description-only
    """Score the visit for the caller."""
    return 17


def missing_returns(patient):  # EXPECT: docstring-missing-returns
    """Score the visit. Args: patient."""
    return 18


def missing_args():  # EXPECT: docstring-missing-args
    """Score the visit. Returns: int score."""
    return 19


def three_line(patient):
    """Score the visit.
    Args: patient.
    Returns: int score."""
    return 20


def test_skip():
    return 21


def test_score_levels():  # EXPECT: repeated-literal-asserts
    assert score_visit("low") == 1
    assert score_visit("mid") == 2
    assert score_visit("high") == 3


def test_names():
    assert score_visit(left) == expected_left
    assert score_visit(middle) == expected_middle
    assert score_visit(right) == expected_right


def test_low_visit():  # EXPECT: sibling-literal-tests
    assert score_visit("low") == 1


def test_mid_visit():
    assert score_visit("mid") == 2


def test_high_visit():
    assert score_visit("high") == 3


def helper_literals():
    """Check three literals outside a test. Args: none. Returns: none."""
    assert score_visit("low") == 1
    assert score_visit("mid") == 2
    assert score_visit("high") == 3


def first_constant():  # EXPECT: same-body
    """Return one. Args: none. Returns: int."""
    return 1


def second_constant():
    """Return one too. Args: none. Returns: int."""
    return 1


def wrap_score(patient):  # EXPECT: wrapper-call
    """Forward the visit. Args: patient. Returns: int score."""
    return score_visit(patient)


def nested_checks(patient):
    """Score the visit. Args: patient. Returns: int score."""
    if patient:  # EXPECT: nested-block
        if ready:
            return 22
    return 23


def filter_items(items):
    """Filter the rows. Args: items. Returns: none."""
    with context:  # EXPECT: nested-block
        for item in items:
            report_patient(item)


def reset_checks(patient):
    """Reset nesting at the inner function. Args: patient. Returns: int score."""
    if patient:
        def inner():
            """Inner score. Args: none. Returns: int score."""
            if ready:
                return 24
            return 25
        return inner()
    return 26


def elif_checks(patient):
    """Choose one branch. Args: patient. Returns: int score."""
    if patient:
        return 27
    elif ready:
        return 28
    return 29


def collect_names(items):
    """Collect names. Args: items. Returns: list names."""
    return [name for name in items if name]


def check_patient(patient: Patient) -> int:
    """Score the visit. Args: patient. Returns: int score."""
    if isinstance(patient, Patient):  # EXPECT: redundant-type-check
        return 30
    if type(patient) is Patient:  # EXPECT: redundant-type-check
        return 31
    return 32


def check_loose(patient: Patient | None) -> int:
    """Score the visit. Args: patient. Returns: int score."""
    if isinstance(patient, Patient):
        return 33
    return 34


def check_assigned() -> int:
    """Score the visit. Args: none. Returns: int score."""
    patient: Patient = load_patient()
    if isinstance(patient, Patient):  # EXPECT: redundant-type-check
        return 35
    return 36


def catch_short():
    """Catch a failure. Args: none. Returns: none."""
    try:  # EXPECT: defensive-handler
        work()
    except Error as e:  # EXPECT: short-name
        report_work()


def allow_handler():
    """Catch a failure on purpose. Args: none. Returns: none."""
    try:  # obliterator-allow ALLOW: defensive-handler
        work()
    except Error:
        report_work()


def release_handler():
    """Release a guard. Args: none. Returns: none."""
    try:
        work()
    finally:
        release()


def read_short(patient):
    """Read a short chain. Args: patient. Returns: int score."""
    return patient.visit.record.code


def read_chain(patient):
    """Read a long chain. Args: patient. Returns: int score."""
    return patient.visit.record.code.value  # EXPECT: long-chain


@property
@classmethod
def both_kinds(cls):  # EXPECT: multiple-decorators
    """Return one kind. Args: cls. Returns: int."""
    return 37


@staticmethod
def single_kind():
    """Return another kind. Args: none. Returns: int."""
    return 38


class FirstRecord:  # EXPECT: multiple-classes
    pass


class SecondRecord:  # EXPECT: multiple-classes
    pass


class ChildRecord(ParentRecord):  # EXPECT: multiple-classes EXPECT: inherits
    pass


class PlainError(Exception):  # EXPECT: multiple-classes
    pass


class BaseFailure(BaseException):  # EXPECT: multiple-classes
    pass


class ColorName(Enum):  # EXPECT: multiple-classes
    pass


class ShadeName(enum.Enum):  # EXPECT: multiple-classes
    pass


class ValueWrapper(ValueError):  # EXPECT: multiple-classes EXPECT: inherits
    pass


class JoinedRecord(Exception, Mixin):  # EXPECT: multiple-classes EXPECT: inherits
    pass


class EmptyRecord():  # EXPECT: multiple-classes
    pass
