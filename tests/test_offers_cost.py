import pytest

from app.offers.cost import InvalidCostInputError, total_cost


def test_a_rate_above_zero_charges_interest_on_top_of_the_fee():
    assert total_cost(100000, 1000, 2, 5000) == 20238


def test_a_higher_rate_and_no_fee_still_costs_more_in_interest_alone():
    assert total_cost(100000, 2000, 2, 0) == 30910


def test_a_zero_rate_costs_exactly_the_fee_with_no_annuity_factor():
    assert total_cost(100000, 0, 2, 5000) == 5000


def test_a_zero_term_is_refused_instead_of_dividing_by_zero():
    with pytest.raises(InvalidCostInputError):
        total_cost(100000, 1000, 0, 5000)


def test_a_negative_term_is_refused_the_same_way_as_zero():
    with pytest.raises(InvalidCostInputError):
        total_cost(100000, 1000, -3, 5000)


def test_a_negative_rate_is_refused_instead_of_answering_a_negative_cost():
    with pytest.raises(InvalidCostInputError):
        total_cost(100000, -100, 12, 5000)
