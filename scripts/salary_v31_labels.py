"""v3.1 retains explicit MONTH header metadata omitted by the slash-only v3 parser."""

from scripts.data_cleaning import fold, parse_salary
from scripts.salary_v3_labels import CENSOR
from scripts.salary_v3_labels import direct_label as body_label


def direct_label(raw):
    label, reason = body_label(raw)
    if reason not in {None, "no_direct_bounded_monthly_vnd_range"}:
        return label, reason
    header = parse_salary(raw.get("salary"))
    low, high = header["salary_min"], header["salary_max"]
    if (
        header["currency"] == "VND"
        and header["salary_period"] == "month"
        and header["salary_basis"] != "net"
        and low is not None
        and high is not None
        and 2e6 <= low < high <= 200e6
        and high / low <= 3
        and not CENSOR.search(fold(raw.get("salary")))
    ):
        if label and (label["low"], label["high"]) != (low, high):
            return None, "conflicting_direct_monthly_ranges"
        return dict(
            low=low,
            high=high,
            salary_monthly_vnd=(low + high) / 2,
            label_quality="direct_month_range_silver",
            field="salary",
            evidence=str(raw["salary"]),
            header_differs=False,
        ), None
    return label, reason
