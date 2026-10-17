import importlib
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd


class CleaningTests(unittest.TestCase):
    def cleaning(self):
        self.assertIsNotNone(
            importlib.util.find_spec("scripts.data_cleaning"),
            "Data-cleaning transformations have not been implemented",
        )
        return importlib.import_module("scripts.data_cleaning")

    def test_salary_units_decimals_and_periods(self):
        parse = self.cleaning().parse_salary
        cases = [
            ("18–25 triệu VND/tháng", 18e6, 25e6, "VND", "month", 21.5e6),
            ("9.4 - 12.0 triệu", 9.4e6, 12e6, "VND", "month", 10.7e6),
            ("8,4 - 12 triệu/tháng", 8.4e6, 12e6, "VND", "month", 10.2e6),
            ("1 triẹu - 40 triẹu/tháng", 1e6, 40e6, "VND", "month", 20.5e6),
            ("200tr-500tr ₫/năm", 200e6, 500e6, "VND", "year", 350e6 / 12),
            ("1,500 - 3,000 USD/năm", 1500, 3000, "USD", "year", 187.5),
            ("500k-1 triệu/tháng", 500000, 1000000, "VND", "month", 750000),
            ("20tr-30tr/tháng", 20e6, 30e6, "VND", "month", 25e6),
        ]
        for text, low, high, currency, period, monthly in cases:
            with self.subTest(text=text):
                result = parse(text, default_period="month" if text == "9.4 - 12.0 triệu" else None)
                self.assertEqual(result["status"], "valid")
                self.assertEqual(result["salary_min"], low)
                self.assertEqual(result["salary_max"], high)
                self.assertEqual(result["currency"], currency)
                self.assertEqual(result["salary_period"], period)
                self.assertAlmostEqual(result["salary_monthly_native"], monthly)

    def test_missing_and_ambiguous_salary_never_become_numeric_targets(self):
        parse = self.cleaning().parse_salary
        cases = {
            None: "missing",
            "Thỏa thuận": "negotiable",
            "0.0 triệu": "not_disclosed",
            "$18tr–22tr /tháng": "ambiguous_currency",
            "$ 500-2,000 /tháng": "ambiguous_currency",
            "18 - 25 triệu": "period_unknown",
            "30 - 20 triệu/tháng": "invalid_range",
            "-10 triệu/tháng": "invalid_amount",
        }
        for text, status in cases.items():
            with self.subTest(text=text):
                result = parse(text)
                self.assertEqual(result["status"], status)
                self.assertIsNone(result["salary_monthly_native"])
        result = parse("1,500-3,000 USD/tháng")
        self.assertEqual(result["salary_monthly_native"], 2250)
        self.assertIsNone(result["salary_monthly_vnd"], "Do not invent an exchange rate")

    def test_one_sided_salary_and_hourly_pay_are_preserved(self):
        parse = self.cleaning().parse_salary
        low = parse("Từ 20 triệu/tháng")
        high = parse("Tới 1,500 USD/tháng")
        self.assertEqual((low["salary_min"], low["salary_max"]), (20e6, None))
        self.assertEqual((high["salary_min"], high["salary_max"]), (None, 1500))
        self.assertIsNone(low["salary_monthly_native"])
        self.assertIsNone(high["salary_monthly_native"])
        hourly = parse("50 - 100 USD/hour")
        self.assertEqual(hourly["salary_period"], "hour")
        self.assertIsNone(hourly["salary_monthly_native"], "Hours per month are unknown")

    def test_experience_preserves_unknowns_ranges_and_months(self):
        parse = self.cleaning().parse_experience
        self.assertIsNone(parse(None)["experience_years"])
        self.assertIsNone(parse("Yêu cầu có kinh nghiệm")["experience_years"])
        self.assertEqual(parse("Không yêu cầu")["experience_years"], 0)
        self.assertEqual(parse("6 tháng")["experience_years"], 0.5)
        self.assertEqual(parse("18 tháng")["experience_years"], 1.5)
        interval = parse("2–4 năm")
        self.assertEqual((interval["experience_min"], interval["experience_max"]), (2, 4))
        self.assertEqual(interval["experience_years"], 2)
        self.assertEqual(interval["experience_kind"], "range_lower_bound")
        self.assertIsNone(parse("Dưới 1 năm")["experience_years"])
        self.assertEqual(parse("100 năm")["experience_kind"], "invalid")

    def test_skills_do_not_confuse_java_with_javascript_or_cpp_with_c(self):
        normalize = self.cleaning().normalize_skills
        skills = normalize('["Java", "JavaScript", "C++", "C#", "NodeJS", "node.js"]')["skills"]
        self.assertEqual(set(skills), {"Java", "JavaScript", "C++", "C#", "Node.js"})
        self.assertEqual(
            normalize("['ReactJS', 'React', 'Postgres']")["skills"], ["PostgreSQL", "React"]
        )
        self.assertFalse(normalize("__import__('os').system('bad')")["valid"])
        self.assertEqual(normalize("python|sql", separator="|")["skills"], ["Python", "SQL"])

    def test_roles_and_multiple_locations_are_not_guessed(self):
        module = self.cleaning()
        self.assertEqual(
            module.classify_role("Senior Backend Python Developer")["role"], "Backend Developer"
        )
        self.assertEqual(module.classify_role("Salesforce Developer")["scope"], "it")
        self.assertEqual(module.classify_role("React Native Developer")["role"], "Mobile Developer")
        self.assertEqual(module.classify_role("Business Developer")["scope"], "non_it")
        self.assertEqual(module.classify_role("Nhân viên kinh doanh phần mềm")["scope"], "non_it")
        self.assertEqual(module.classify_role("Chuyên viên")["scope"], "unknown")
        loc = module.normalize_location("Hà Nội / Hồ Chí Minh (mới)")
        self.assertEqual(loc["locations"], ["Hà Nội", "TP.HCM"])
        self.assertTrue(module.normalize_location("Ha Noi / Remote")["is_remote"])

    def test_partition_deduplication_and_raw_traceability(self):
        module = self.cleaning()
        rows = []
        for ident, title, url, salary, crawl in [
            (
                1,
                "Backend Python Developer",
                "https://example.com/jobs/1",
                "18–25 triệu/tháng",
                "2026-06-01",
            ),
            (
                2,
                "Backend Python Developer",
                "https://example.com/jobs/1",
                "20–30 triệu/tháng",
                "2026-06-02",
            ),
            (
                3,
                "Frontend Developer",
                "https://example.com/hist201800001",
                "10–15 triệu/tháng",
                "2018-01-01",
            ),
            (
                4,
                "Nhân viên kinh doanh",
                "https://example.com/jobs/4",
                "10–15 triệu/tháng",
                "2026-06-01",
            ),
            (5, "Frontend Developer", "https://example.com/jobs/5", "Thỏa thuận", "2026-06-01"),
        ]:
            rows.append(
                dict(
                    id=ident,
                    title=title,
                    source_url=url,
                    salary=salary,
                    crawl_time=crawl,
                    location="Hà Nội",
                    experience="2 năm",
                    skills='["Python"]',
                )
            )
        df = pd.DataFrame(rows)
        before = df.copy(deep=True)
        result = module.clean_source("user_vietnam_it_jobs", df, module.DEFAULT_POLICY)
        pd.testing.assert_frame_equal(df, before)
        self.assertEqual(len(result["audit"]), 5)
        self.assertEqual(len(result["clean"]), 2)
        self.assertEqual(len(result["review"]), 1)
        self.assertEqual(
            result["audit"].disposition.value_counts().to_dict(),
            {"kept": 2, "duplicate": 1, "quarantined_provenance": 1, "non_it": 1},
        )
        kept = result["clean"].set_index("record_id")
        self.assertEqual(kept.loc["user_vietnam_it_jobs:2", "salary_monthly_vnd"], 25e6)
        self.assertTrue(pd.isna(kept.loc["user_vietnam_it_jobs:5", "salary_monthly_vnd"]))
        self.assertNotIn("user_vietnam_it_jobs:3", kept.index)
        self.assertTrue(result["clean"].group_id.is_unique)

    def test_role_regressions_from_actual_source_samples(self):
        classify = self.cleaning().classify_role
        cases = {
            "Viettel Tuyển Dụng iOS Developer": "Mobile Developer",
            "Data Analyst (After Sales Parts Business)": "Data Analyst",
            "Software Engineer, Marketing Platform": "Software Developer",
            "NHÂN VIÊN IT LẬP TRÌNH": "Software Developer",
            "AI Engineer": "ML Engineer",
            "Nhà phát triển .NET cao cấp": "Software Developer",
        }
        for title, role in cases.items():
            with self.subTest(title=title):
                self.assertEqual(classify(title)["role"], role)
        for title in [
            "Nhân Viên Lập Trình CAM",
            "Lập Trình Vận Hành Máy CNC",
            "Tư vấn bán hàng (phần mềm)",
            "QC Lead (Ngành Gỗ)",
            "Giới thiệu Sự kiện Sức mạnh trí tuệ nhân tạo",
            "Mobile Pet Groomer",
            "Giám Sát Chất Lượng Cuộc Gọi Telesales (QA/QC)",
        ]:
            with self.subTest(title=title):
                self.assertNotEqual(classify(title)["scope"], "it")

    def test_multi_position_advertisement_is_not_given_one_salary_role(self):
        m = self.cleaning()
        row = dict(
            id=1,
            title="Tuyển Business Analyst/Software Engineer/QA Engineer",
            salary="10-15 triệu/tháng",
            skills="[]",
            crawl_time="2026-06-01",
            source_url="https://example.com/multi",
        )
        result = m.clean_source("user_vietnam_it_jobs", pd.DataFrame([row]), m.DEFAULT_POLICY)
        self.assertEqual(len(result["clean"]), 0)
        self.assertIn("multiple_roles_one_salary", result["review"].iloc[0].review_reasons)

    def test_native_source_contracts_and_quarantine(self):
        m = self.cleaning()
        raw = pd.DataFrame(
            [
                dict(
                    title="Software Engineer",
                    url="https://example.com/1",
                    is_remote=True,
                    country="US",
                    location_raw="New York",
                    salary_min=120000,
                    salary_max=180000,
                    salary_currency="USD",
                    salary_period="year",
                    skills="Python|SQL",
                ),
                dict(
                    title="QA Specialist",
                    url="https://example.com/2",
                    is_remote=False,
                    salary_min=50000,
                    salary_max=60000,
                    salary_currency="USD",
                    salary_period="year",
                ),
                dict(
                    title="Software Engineer",
                    url="https://example.com/3",
                    is_remote=False,
                    salary_min=5000000,
                    salary_max=6000000,
                    salary_currency="USD",
                    salary_period="year",
                ),
                dict(
                    title="Software Engineer",
                    url="https://example.com/4",
                    salary_min=80,
                    salary_max=118,
                    salary_currency="GBP",
                    salary_period="year",
                ),
            ]
        )
        result = m.clean_source("dataforge_2026_08", raw, m.DEFAULT_POLICY)
        self.assertEqual(len(result["clean"]), 1)
        self.assertTrue(result["clean"].iloc[0].is_remote)
        self.assertEqual(result["clean"].iloc[0].salary_monthly_native, 12500)
        self.assertEqual(len(result["review"]), 3)
        self.assertTrue(
            result["review"].review_reasons.str.contains("role_context_unverified").any()
        )
        row = dict(
            job_title="Python Developer",
            category="công_nghệ_thông_tin_kỹ_thuật_số",
            salary="9.4 - 12.0 triệu",
            salary_min=9,
            salary_max=12,
            technical_skills="['Python']",
            experience_required="6 tháng",
        )
        viet = m.clean_source("vietjobs_2025", pd.DataFrame([row, row]), m.DEFAULT_POLICY)
        self.assertEqual(len(viet["clean"]), 1)
        self.assertTrue(viet["clean"].iloc[0].salary_text_corrected_numeric)
        self.assertEqual(viet["clean"].iloc[0].salary_monthly_vnd, 10700000)
        self.assertEqual(viet["clean"].iloc[0].experience_years, 0.5)

    def test_survey_label_export_keeps_annual_target_and_excludes_leakage(self):
        from scripts import clean_data

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / clean_data.INPUTS["stackoverflow_2025"]
            path.parent.mkdir(parents=True)
            rows = []
            for ident, profession, annual in [
                (1, "I am a developer by profession", 120000),
                (2, "I code primarily as a hobby", 120000),
                (3, "I am a developer by profession", 50000000),
                (4, "I am a developer by profession", 0),
            ]:
                rows.append(
                    dict(
                        ResponseId=ident,
                        MainBranch=profession,
                        ConvertedCompYearly=annual,
                        DevType="Developer, full-stack",
                        WorkExp=5,
                        Country="Vietnam",
                        LanguageHaveWorkedWith="Python;SQL",
                        DatabaseHaveWorkedWith="PostgreSQL",
                        PlatformHaveWorkedWith="",
                        WebframeHaveWorkedWith="FastAPI",
                    )
                )
            pd.DataFrame(rows).to_csv(path, index=False)
            with patch.object(clean_data, "ROOT", root):
                stats = clean_data.process(
                    "stackoverflow_2025", self.cleaning().DEFAULT_POLICY, root / "cleaned"
                )
            self.assertEqual(stats["label_rows"], 1)
            labels = pd.read_csv(root / stats["files"]["labels"][0]["path"])
            self.assertEqual(labels.compensation_annual_usd.tolist(), [120000])
            self.assertEqual(labels.record_id.tolist(), ["stackoverflow_2025:1"])
            for forbidden in ["salary_min", "salary_max", "salary_raw", "description", "title"]:
                self.assertNotIn(forbidden, labels)


if __name__ == "__main__":
    unittest.main()
