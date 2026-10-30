"""Streamlit seam consumes synthetic prepared rows, including parent overlays."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

from career_market.company_service import CompanyMarketService as MarketService

PAGE = Path(__file__).parents[1] / "pages/10_Cong_ty.py"


def test_company_page_displays_the_service_groups_provenance_and_csv():
    rows = [
        {
            "source_id": "fixture",
            "posting_id": "1",
            "company_raw": " Alpha ",
            "locations": ["HCM", "HN"],
            "salary_label_status": "accepted",
        },
        {"source_id": "fixture", "posting_id": "2", "company_raw": "ALPHA"},
        {"source_id": "fixture", "posting_id": "3", "company_raw": ""},
    ]
    app = AppTest.from_file(str(PAGE))
    app.session_state["company_prepared_rows"] = rows
    app.run()
    assert not app.exception
    expected = MarketService().company_report(rows)
    assert [m.value for m in app.metric] == ["3", "3", "1", "2", "1"]
    assert app.dataframe[0].value["group_id"].tolist() == [
        r["group_id"] for r in expected["aliases"]
    ]
    assert app.dataframe[1].value["group_id"].tolist() == [
        r["group_id"] for r in expected["groups"]
    ]
    assert app.dataframe[2].value["source_id"].tolist() == ["fixture"] * 3
    assert len(app.get("download_button")) == 4
    assert any("70/15/15" in text.value for text in app.info)
    assert app.session_state["company_prepared_rows"] == rows
