"""Posting identity and physical/work-mode selection shared across reports."""

import json
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


def posting_key(source_id, url, job_id=None):
    parts = urlsplit(url or "")
    if parts.scheme in {"http", "https"} and parts.netloc:
        # Observed TopCV links identify the job in the path; these two keys
        # describe the search click, not a second job. Unknown keys stay intact.
        source_tracking = (
            {"ta_source", "u_sr_id"} if parts.hostname in {"topcv.vn", "www.topcv.vn"} else set()
        )
        query = sorted(
            (key, value)
            for key, value in parse_qsl(parts.query, keep_blank_values=True)
            if not key.casefold().startswith("utm_")
            and key.casefold() not in {"gclid", "fbclid", "msclkid"}
            and key.casefold() not in source_tracking
        )
        canonical = urlunsplit(
            ("https", parts.netloc.lower(), parts.path.rstrip("/"), urlencode(query), "")
        )
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
