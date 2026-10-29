"""Posting identity and physical/work-mode selection shared across reports."""

import json
from urllib.parse import urlsplit, urlunsplit


def posting_key(source_id, url, job_id=None):
    parts = urlsplit(url or "")
    if parts.scheme in {"http", "https"} and parts.netloc:
        canonical = urlunsplit(("https", parts.netloc.lower(), parts.path.rstrip("/"), "", ""))
        return f"{source_id}:{canonical}"
    if job_id:
        return f"{source_id}:id:{job_id}"
    raise ValueError("Tin thiếu ID/URL có thể đối chiếu.")


def values(value):
    return json.loads(value) if isinstance(value, str) else (value or [])


def select_locations(rows, locations=None, work_mode=None):
    selected = {}
    for row in rows:
        if locations and not set(locations).intersection(values(row.get("locations"))):
            continue
        if work_mode and work_mode not in values(row.get("work_modes")):
            continue
        key = row.get("posting_id") or posting_key(
            row["source_id"], row.get("job_url"), row.get("job_id")
        )
        selected.setdefault(key, row)
    return list(selected.values())
