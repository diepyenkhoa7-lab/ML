"""Evaluation in original units, with small-group support explicitly reported."""

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from .data import UNITS


def metrics(frame, predictions):
    frame = frame.copy()
    frame["prediction"] = np.asarray(predictions)
    frame["experience_band"] = pd.cut(
        frame.experience_years, [-1, 2, 5, 10, 80], labels=["0-2", "3-5", "6-10", "11+"]
    )
    result = {"by_market": {}, "by_role": {}, "by_experience": {}}
    for name, columns in [
        ("by_market", ["market"]),
        ("by_role", ["market", "role"]),
        ("by_experience", ["market", "experience_band"]),
    ]:
        for group, part in frame.groupby(columns, observed=True):
            group = group if isinstance(group, tuple) else (group,)
            y, predicted = part.salary, part.prediction
            result[name][" | ".join(map(str, group))] = dict(
                samples=len(y),
                unit=UNITS[group[0]],
                mae=float(mean_absolute_error(y, predicted)),
                rmse=float(np.sqrt(mean_squared_error(y, predicted))),
                r2=float(r2_score(y, predicted)) if len(y) > 1 and y.nunique() > 1 else None,
                low_support=len(y) < 10,
            )
    return result
