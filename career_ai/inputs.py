"""File input contracts shared by notebook and CLI."""

import json

import pandas as pd


def read_profiles(path):
    suffix = path.suffix.lower()
    if suffix == ".json":
        records = json.loads(path.read_text())
        if not isinstance(records, list) or any(not isinstance(r, dict) for r in records):
            raise ValueError("JSON input must be an array of profile objects")
        frame = pd.DataFrame(records)
    elif suffix == ".xlsx":
        frame = pd.read_excel(path)
    elif suffix == ".csv":
        frame = pd.read_csv(path)
    else:
        raise ValueError("Input must be CSV, XLSX or JSON")
    return frame.astype(object).where(pd.notna(frame), None)


def missing(value):
    return value is None or (isinstance(value, str) and not value.strip())
