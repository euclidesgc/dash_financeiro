from app.offers.cost import total_cost


def test_a_rate_above_zero_charges_interest_on_top_of_the_fee():
    assert total_cost(100000, 1000, 2, 5000) == 20238


def test_a_higher_rate_and_no_fee_still_costs_more_in_interest_alone():
    assert total_cost(100000, 2000, 2, 0) == 30910


def test_a_zero_rate_costs_exactly_the_fee_with_no_annuity_factor():
    assert total_cost(100000, 0, 2, 5000) == 5000
