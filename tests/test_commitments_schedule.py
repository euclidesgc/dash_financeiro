from datetime import date

from app.commitments.schedule import (
    consecutive_run,
    end_month,
    median_day,
    on_month,
)


def test_an_even_number_of_days_takes_the_lower_middle():
    assert median_day([10, 12, 20, 22]) == 12


def test_an_odd_number_of_days_takes_the_middle_one():
    assert median_day([16, 16, 16, 17, 18, 19, 28, 31, 31]) == 18


def test_the_predicted_day_is_always_a_day_the_series_had():
    days = [6, 16, 17, 18, 19, 28, 31]
    assert median_day(days) in days


def test_a_day_the_month_does_not_have_falls_on_its_last():
    assert on_month(31, date(2026, 11, 1)) == date(2026, 11, 30)


def test_a_day_the_month_has_is_kept():
    assert on_month(11, date(2026, 11, 1)) == date(2026, 11, 11)


def test_february_of_a_leap_year_stops_at_its_last_day():
    assert on_month(30, date(2028, 2, 1)) == date(2028, 2, 29)


def test_the_end_month_crosses_the_year():
    assert end_month("2026-08", 22) == "2028-06"


def test_the_end_month_of_the_last_remaining_installments():
    assert end_month("2026-08", 2) == "2026-10"


def test_a_series_with_nothing_left_ends_in_the_month_it_was_last_seen():
    assert end_month("2026-09", 0) == "2026-09"


def test_the_longest_run_ignores_the_gap():
    assert consecutive_run(["2026-01", "2026-02", "2026-04", "2026-05", "2026-06"]) == 3


def test_a_single_month_is_a_run_of_one():
    assert consecutive_run(["2026-01"]) == 1
