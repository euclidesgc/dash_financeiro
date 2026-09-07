import dataclasses
from datetime import date

import pytest

from app.routers.reference import EARLIEST, LATEST, Reference, screen_date

REFERENCE = date(2026, 9, 5)


@pytest.fixture(autouse=True)
def fixed_clock(monkeypatch):
    monkeypatch.setenv("DASH_TODAY", REFERENCE.isoformat())


def test_the_range_constants_hold_the_agreed_boundaries():
    assert (EARLIEST, LATEST) == (date(2000, 1, 1), date(2100, 12, 31))


def test_the_reference_is_a_frozen_dataclass_with_the_three_fields():
    reference = screen_date(None)

    assert isinstance(reference, Reference)
    assert {field.name for field in dataclasses.fields(Reference)} == {"date", "asked", "notice"}
    with pytest.raises(dataclasses.FrozenInstanceError):
        reference.asked = True


def test_no_query_string_answers_with_the_reference_date_unasked():
    reference = screen_date(None)

    assert (reference.date, reference.asked, reference.notice) == (REFERENCE, False, None)


def test_a_blank_parameter_is_absence_not_refusal():
    empty = screen_date("")
    spaces = screen_date("   ")

    assert (empty.date, empty.asked, empty.notice) == (REFERENCE, False, None)
    assert (spaces.date, spaces.asked, spaces.notice) == (REFERENCE, False, None)


def test_both_range_limits_are_accepted_not_assumed():
    lower = screen_date("2000-01-01")
    upper = screen_date("2100-12-31")

    assert (lower.date, lower.asked, lower.notice) == (date(2000, 1, 1), True, None)
    assert (upper.date, upper.asked, upper.notice) == (date(2100, 12, 31), True, None)


def test_an_unreadable_date_is_refused_with_the_shared_phrase():
    reference = screen_date("banana")

    assert (reference.date, reference.asked) == (REFERENCE, False)
    assert reference.notice == "data inválida: data (banana)"


def test_a_readable_date_outside_the_range_is_refused_without_raising():
    below = screen_date("0001-01-01")
    above = screen_date("2101-01-01")

    assert (below.date, below.asked) == (REFERENCE, False)
    assert below.notice == "data inválida: data (0001-01-01)"
    assert (above.date, above.asked) == (REFERENCE, False)
    assert above.notice == "data inválida: data (2101-01-01)"


def test_the_immediate_neighbours_outside_the_range_are_refused_too():
    below = screen_date("1999-12-31")
    above = screen_date("2101-01-01")

    assert (below.date, below.asked) == (REFERENCE, False)
    assert below.notice == "data inválida: data (1999-12-31)"
    assert (above.date, above.asked) == (REFERENCE, False)
    assert above.notice == "data inválida: data (2101-01-01)"


def test_a_missing_dash_today_falls_back_to_the_clock(monkeypatch):
    monkeypatch.delenv("DASH_TODAY", raising=False)

    assert screen_date(None).date == date.today()
