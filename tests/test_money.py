import pytest

from app.ingest.money import FractionalCentsError, to_cents


def test_converts_two_decimal_places():
    assert to_cents(2462.56) == 246256
    assert to_cents(-3310.23) == -331023
    assert to_cents("8666.70") == 866670
    assert to_cents(0) == 0


def test_does_not_lose_the_cent_that_raw_float_multiplication_loses():
    assert int(1.15 * 100) == 114
    assert to_cents(1.15) == 115


def test_refuses_a_value_that_is_not_whole_cents():
    with pytest.raises(FractionalCentsError):
        to_cents(10.005)
