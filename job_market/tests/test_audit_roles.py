"""Audit role regressions through MarketService; fixtures are not market data."""

import pytest

from career_market import MarketService


def test_actual_mobile_game_tester_title_requires_role_review():
    title = (
        "Mobile Game Tester (QA) - Từ 01 Năm Kinh Nghiệm Trở Lên - Thu Nhập Hấp Dẫn Theo Năng Lực"
    )
    result = MarketService().classify_role(title)

    assert (result["role"], result["role_status"]) == (None, "review")
    assert result["role_reason"]


def test_backend_developer_is_not_excluded_by_marketing_product_domain():
    result = MarketService().classify_role("Backend Developer - Marketing Platform")

    assert (result["role"], result["role_status"]) == ("Backend", "matched")
    assert result["role_evidence"] == [{"field": "title", "text": "Backend"}]


@pytest.mark.parametrize(
    ("title", "description", "requirements", "role", "status"),
    [
        ("Manual QA", "", "QA Automation, Flutter", None, "review"),
        ("Mobile QA Engineer", "", "QA Automation", None, "review"),
        ("Android Tester", "Develop test cases for Android applications.", "", None, "review"),
        ("Mobile QA Automation Engineer", "", "", "QA Automation", "matched"),
        ("Software Tester (Manual & Automation)", "", "", "QA Automation", "matched"),
        ("Mobile Developer / QA Automation Engineer", "", "", None, "review"),
        ("Backend Developer - Sales Platform", "", "", "Backend", "matched"),
        ("Frontend Engineer - Marketing Platform", "", "", "Frontend", "matched"),
        ("Backend Developer - PLC Software", "", "", None, "out_of_scope"),
        ("Marketing Manager - Backend Developer", "", "", None, "out_of_scope"),
    ],
)
def test_testing_occupations_product_domains_and_ambiguity_stay_distinct(
    title, description, requirements, role, status
):
    result = MarketService().classify_role(title, description, requirements)

    assert (result["role"], result["role_status"]) == (role, status)
    assert result["role_reason"]
    for item in result["role_evidence"]:
        assert item["text"] in {"title": title, "description": description}[item["field"]]
