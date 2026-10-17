"""Published aggregate reference, kept separate from individual model predictions."""

import math

import pandas as pd

from backend.app.services.data import ROOT


def market_reference(role, experience, prediction):
    source = "ITviec 2025–2026"
    url = "https://itviec.com/bao-cao/luong-it-va-thi-truong-tuyen-dung-it-vietnam"
    result = dict(
        available=False,
        source=source,
        source_url=url,
        role=role,
        experience_band=None,
        median_vnd_month=None,
        prediction_minus_median_vnd=None,
        caution=(
            "Trung vị thu nhập khảo sát theo nhóm, không phải lương chào tuyển "
            "hay nhãn thực tế của hồ sơ này; không dùng để sửa dự đoán."
        ),
    )
    if experience is None:
        return result
    years = math.floor(experience)
    references = pd.read_csv(ROOT / "data/references/itviec_2025_2026.csv")
    matched = references[
        references.role.eq(role) & references.low_years.le(years) & references.high_years.ge(years)
    ]
    if len(matched):
        row = matched.iloc[0]
        result.update(
            available=True,
            experience_band=row.experience_band,
            median_vnd_month=int(row.median_vnd_month),
            prediction_minus_median_vnd=round(prediction - row.median_vnd_month),
        )
    return result
