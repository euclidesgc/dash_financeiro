import pytest

from app.taxonomy.limits import is_whole_month, signal_for


@pytest.mark.parametrize("spent_cents", [0, 999])
def test_signal_for_without_a_limit_is_none(spent_cents):
    assert signal_for(spent_cents, None) is None


@pytest.mark.parametrize("spent_cents,limit_cents", [(0, 100), (79, 100)])
def test_signal_for_below_eighty_percent_is_within(spent_cents, limit_cents):
    assert signal_for(spent_cents, limit_cents) == "within"


@pytest.mark.parametrize("spent_cents,limit_cents", [(80, 100), (100, 100), (4, 5)])
def test_signal_for_from_eighty_percent_to_the_limit_is_warning(spent_cents, limit_cents):
    assert signal_for(spent_cents, limit_cents) == "warning"


def test_signal_for_above_the_limit_is_over():
    assert signal_for(101, 100) == "over"


@pytest.mark.parametrize(
    "date_from,date_to",
    [
        ("2026-08-01", "2026-08-31"),
        ("2026-02-01", "2026-02-28"),
        ("2024-02-01", "2024-02-29"),
    ],
)
def test_is_whole_month_accepts_the_first_and_last_day_of_the_same_month(date_from, date_to):
    assert is_whole_month(date_from, date_to) is True


@pytest.mark.parametrize(
    "date_from,date_to",
    [
        ("2026-08-01", "2026-08-30"),
        ("2026-08-02", "2026-08-31"),
        ("2026-07-01", "2026-08-31"),
        (None, "2026-08-31"),
        ("2026-08-01", None),
        (None, None),
    ],
)
def test_is_whole_month_refuses_partial_intervals_and_missing_bounds(date_from, date_to):
    assert is_whole_month(date_from, date_to) is False
