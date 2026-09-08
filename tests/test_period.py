from datetime import date

import pytest

from app.queries.period import (
    InvalidPeriodError,
    check_period,
    covers_whole_months,
    default_period,
    month_end,
)


def test_the_default_period_opens_on_the_first_day_of_the_running_month():
    assert default_period(date(2026, 9, 5)) == ("2026-09-01", "2026-09-05")


def test_the_default_period_on_the_first_day_of_the_month_is_a_single_day():
    assert default_period(date(2026, 9, 1)) == ("2026-09-01", "2026-09-01")


def test_the_default_period_never_reaches_past_the_reference_date():
    start, end = default_period(date(2026, 9, 5))
    assert end == "2026-09-05"


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


def test_the_month_end_of_a_leap_february_is_the_twenty_ninth():
    assert month_end(date(2024, 2, 10)) == date(2024, 2, 29)


def test_the_month_end_crosses_the_turn_of_the_year():
    assert month_end(date(2025, 12, 3)) == date(2025, 12, 31)


def test_a_window_from_the_first_to_the_last_day_of_the_month_covers_whole_months():
    assert covers_whole_months("2026-03-01", "2026-08-31") is True


def test_a_window_starting_after_the_first_day_does_not_cover_whole_months():
    assert covers_whole_months("2026-03-02", "2026-08-31") is False


def test_a_window_ending_before_the_last_day_of_the_month_does_not_cover_whole_months():
    assert covers_whole_months("2026-03-01", "2026-08-30") is False
