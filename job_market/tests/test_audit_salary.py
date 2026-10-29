"""Synthetic salary notation cases lock parser behavior, never training labels."""

import pytest

from career_market import MarketService


@pytest.mark.parametrize(
    "raw",
    [
        "20 triệu - 30.000.000 VND/tháng",
        "20.000.000 - 30 triệu VND/tháng",
        "20000000 - 30 triệu VND/tháng",
        "20 triệu - 30000000 VND/tháng",
    ],
)
def test_mixed_full_amount_and_scale_has_twenty_five_million_midpoint(raw):
    result = MarketService().normalize_salary(raw)
    assert (
        result["salary_lower"],
        result["salary_upper"],
        result["salary_target_vnd_month"],
    ) == (20_000_000, 30_000_000, 25_000_000)


def test_adjacent_dong_symbol_is_currency_evidence():
    result = MarketService().normalize_salary("20.000.000đ/tháng")
    assert (result["salary_currency"], result["salary_target_vnd_month"]) == ("VND", 20_000_000)


@pytest.mark.parametrize("factor", [1, 1000])
def test_four_digit_shorthand_keeps_shared_thousand_suffix(factor):
    result = MarketService().normalize_salary(f"{1000 * factor}–{2000 * factor} nghìn VND/tháng")
    assert (result["salary_lower"], result["salary_upper"], result["salary_target_vnd_month"]) == (
        1_000_000 * factor,
        2_000_000 * factor,
        1_500_000 * factor,
    )


def test_grouped_thousand_endpoints_can_share_a_suffix():
    result = MarketService().normalize_salary("1.000–2.000 nghìn VND/tháng")
    assert result["salary_target_vnd_month"] == 1_500_000
