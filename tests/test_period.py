from datetime import date

import pytest

from app.queries.period import (
    CLOSED_MONTHS,
    InvalidPeriodError,
    check_period,
    default_period,
)


def test_the_default_period_ends_on_the_last_closed_month():
    assert default_period(date(2026, 9, 6)) == ("2026-03-01", "2026-08-31")


def test_the_first_day_of_a_month_still_looks_at_the_month_before():
    assert default_period(date(2026, 9, 1)) == ("2026-03-01", "2026-08-31")


def test_the_default_period_crosses_the_turn_of_the_year():
    assert default_period(date(2026, 2, 14)) == ("2025-08-01", "2026-01-31")


def test_the_default_period_spans_six_closed_months():
    start, end = default_period(date(2026, 9, 6))
    first, last = date.fromisoformat(start), date.fromisoformat(end)
    assert CLOSED_MONTHS == 6
    assert (last.year - first.year) * 12 + last.month - first.month + 1 == CLOSED_MONTHS
    assert first.day == 1


def test_the_length_of_the_default_period_is_a_parameter():
    assert default_period(date(2026, 9, 6), months=1) == ("2026-08-01", "2026-08-31")


def test_a_february_of_a_leap_year_ends_on_the_twenty_ninth():
    assert default_period(date(2024, 3, 10), months=1) == ("2024-02-01", "2024-02-29")


def test_a_period_of_one_day_is_accepted():
    assert check_period("2026-03-01", "2026-03-01") == (date(2026, 3, 1), date(2026, 3, 1))


def test_an_inverted_period_is_refused_naming_both_fields():
    with pytest.raises(InvalidPeriodError) as refused:
        check_period("2026-03-01", "2026-01-31")
    assert str(refused.value) == "período inválido: fim (2026-01-31) anterior a inicio (2026-03-01)"


def test_a_missing_date_is_refused_naming_the_field():
    with pytest.raises(InvalidPeriodError) as refused:
        check_period(None, "2026-08-31")
    assert str(refused.value) == "data inválida: inicio (None)"
