import importlib
import unittest

import pandas as pd


def module():
    return importlib.import_module("scripts.label_review")


def fixture(ident, **changes):
    row = dict(
        record_id=ident,
        group_id=ident,
        source_dataset="vietjobs_2025",
        title="Python Developer",
        country="Vietnam",
        location="Hà Nội",
        company=None,
        description=None,
        skills="Python;SQL",
        skills_json='["Python", "SQL"]',
        skills_missing=False,
        experience_years=2,
        experience_missing=False,
        role="Software Developer",
        salary_min=20e6,
        salary_max=30e6,
        salary_period="month",
        salary_basis="unknown",
        currency="VND",
        target=25e6,
        cohort="vn_it",
        platform=None,
        source_url=None,
    )
    row.update(changes)
    return row


class LabelReviewTests(unittest.TestCase):
    def test_ambiguous_labels_and_wrong_role_are_quarantined(self):
        m = module()
        rows = [
            fixture("good"),
            fixture("wide", salary_min=1e6, salary_max=40e6, target=20.5e6),
            fixture("footwear", title="Footwear QC Inspector", role="QA Engineer"),
            fixture(
                "ybox",
                source_dataset="user_vietnam_it_jobs",
                platform="ybox",
                skills_missing=True,
                description=None,
            ),
            fixture("mismatch", target=99e6),
            fixture("mold", title="Nhân Viên Lập Trình Khuôn Mẫu"),
            fixture("overseas", description="Tuyển thẳng sang Nhật làm sau khi xin visa."),
            fixture("foreign_country", country="Nhật Bản", location="Nhật Bản"),
        ]
        result = m.review_labels(pd.DataFrame(rows), m.DEFAULT_POLICY)
        self.assertEqual(result.set_index("record_id").loc["good", "review_status"], "accepted")
        self.assertTrue(result.loc[result.record_id.ne("good"), "review_status"].eq("review").all())
        self.assertEqual(rows[0]["target"], 25e6)

    def test_hard_duplicates_collapse_and_conflicts_quarantine_all(self):
        m = module()
        rows = [
            fixture("a", group_id="same"),
            fixture("b", group_id="same"),
            fixture("c", group_id="conflict"),
            fixture("d", group_id="conflict", target=30e6, salary_max=40e6),
        ]
        result = m.review_labels(pd.DataFrame(rows), m.DEFAULT_POLICY)
        statuses = result.set_index("record_id").review_status.to_dict()
        self.assertEqual(
            statuses, {"a": "accepted", "b": "duplicate", "c": "review", "d": "review"}
        )
        self.assertTrue(
            result.loc[result.record_id.isin(["c", "d"]), "review_reasons"]
            .str.contains("conflicting_labels_same_identity")
            .all()
        )

    def test_groups_use_identity_and_content_without_salary(self):
        m = module()
        body = "Build Python distributed services and maintain database operations. " * 8
        rows = [
            fixture("a", description=body, company="Example"),
            fixture("b", description=body + "Apply now.", source_dataset="user_vietnam_it_jobs"),
            fixture("c", cohort="survey", source_dataset="stackoverflow_2025"),
            fixture("d", cohort="survey", source_dataset="stackoverflow_2025"),
        ]
        result, edges = m.group_records(pd.DataFrame(rows), m.DEFAULT_POLICY)
        groups = result.set_index("record_id").leakage_group_id
        self.assertEqual(groups["a"], groups["b"])
        self.assertNotEqual(groups["c"], groups["d"], "Similar respondents are distinct people")
        rows[0]["target"] = 99999999
        changed, _ = m.group_records(pd.DataFrame(rows), m.DEFAULT_POLICY)
        pd.testing.assert_series_equal(
            groups.sort_index(), changed.set_index("record_id").leakage_group_id.sort_index()
        )
        self.assertGreater(len(edges), 0)

    def test_split_is_deterministic_disjoint_and_keeps_groups(self):
        m = module()
        rows = pd.DataFrame([fixture(f"r{i}", leakage_group_id=f"g{i // 2}") for i in range(200)])
        assigned = m.assign_splits(rows, seed=42, fractions=[0.7, 0.15, 0.15])
        changed = m.assign_splits(
            rows.sample(frac=1, random_state=9), seed=42, fractions=[0.7, 0.15, 0.15]
        )
        self.assertEqual(assigned.groupby("leakage_group_id").split.nunique().max(), 1)
        self.assertEqual(
            assigned.split.value_counts().to_dict(), {"train": 140, "test": 30, "valid": 30}
        )
        pd.testing.assert_series_equal(
            assigned.set_index("record_id").split.sort_index(),
            changed.set_index("record_id").split.sort_index(),
        )
        with self.assertRaises(ValueError):
            m.assign_splits(rows.iloc[:2], seed=42, fractions=[0.7, 0.15, 0.15])

    def test_company_and_location_numbers_are_identity_not_salary(self):
        m = module()
        rows = [
            fixture("a", source_dataset="dataforge_2026_08", company="Company 1"),
            fixture("b", source_dataset="dataforge_2026_08", company="Company 2"),
        ]
        grouped, _ = m.group_records(pd.DataFrame(rows), m.DEFAULT_POLICY)
        self.assertEqual(grouped.leakage_group_id.nunique(), 2)


if __name__ == "__main__":
    unittest.main()
