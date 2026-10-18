"""Bounded public JobPosting collection. No accounts, hidden APIs or salary inference."""

import argparse
import hashlib
import json
import re
import sys
import time
import urllib.robotparser
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlsplit

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.data_cleaning import fold  # noqa: E402

DEVELOPER = re.compile(
    r"develop|software|lap trinh|backend|back.end|frontend|front.end|full.stack|"
    r"embedded|data engineer|ky su phan mem|\b(?:ai|ml) engineer"
)
AGENT = "MLCourseworkSalaryResearch/3.0 (public job metadata; bounded requests)"


def collect(source="careerlink_topdev"):
    folder_name = "joboko_20261018" if source == "joboko" else "public_jobs_20261018"
    folder = ROOT / "data/raw" / folder_name
    folder.mkdir(exist_ok=True)
    cache = ROOT / ".cache/salary_v3_public"
    cache.mkdir(parents=True, exist_ok=True)
    if (folder / "manifest.json").exists():
        raise ValueError("Frozen collection exists; do not overwrite")
    session = requests.Session()
    session.headers["User-Agent"] = AGENT
    robots = {}
    requests_log = []
    blocked = []

    def get(url):
        origin = f"{urlsplit(url).scheme}://{urlsplit(url).netloc}"
        if origin not in robots:
            response = session.get(origin + "/robots.txt", timeout=30)
            response.raise_for_status()
            policy = urllib.robotparser.RobotFileParser()
            policy.parse(response.text.splitlines())
            robots[origin] = policy
            (folder / (urlsplit(url).netloc + ".robots.txt")).write_text(response.text)
        if not robots[origin].can_fetch(AGENT, url):
            raise ValueError("robots.txt disallows " + url)
        path = cache / (hashlib.sha256(url.encode()).hexdigest() + ".html")
        if not path.exists():
            time.sleep(max(2, robots[origin].crawl_delay(AGENT) or 0))
            response = session.get(url, timeout=30)
            requests_log.append(dict(url=url, status=response.status_code))
            if response.status_code in {403, 429}:
                blocked.append(dict(url=url, status=response.status_code))
                return None
            response.raise_for_status()
            path.write_text(response.text)
        soup = BeautifulSoup(path.read_text(), "html.parser")
        visible = fold(soup.get_text(" ", strip=True))
        if any(
            marker in visible
            for marker in [
                "xac nhan ban khong phai robot",
                "verify you are human",
                "access denied",
                "checking your browser",
                "just a moment...",
            ]
        ):
            blocked.append(dict(url=url, status="challenge_in_200_response"))
            return None
        return soup

    starts = [
        "https://www.careerlink.vn/viec-lam/cntt-phan-mem/19",
        "https://topdev.vn/jobs/search?keyword=developer",
    ]
    if source == "joboko":
        starts = ["https://vn.joboko.com/tim-viec-lam-lap-trinh-vien"]
    links, visited, pending = set(), set(), list(starts)
    while pending and len(visited) < (6 if source == "joboko" else 12):
        url = pending.pop(0)
        if url in visited:
            continue
        soup = get(url)
        if soup is None:
            break
        visited.add(url)
        for anchor in soup.find_all("a", href=True):
            href = urljoin(url, anchor["href"])
            if any(k in href for k in ["/tim-viec-lam/", "/detail-jobs/"]) or re.search(
                r"xvi\d+", href
            ):
                if DEVELOPER.search(fold(anchor.get_text(" ", strip=True))):
                    links.add(href.split("?")[0])
            elif "/viec-lam/cntt-phan-mem/19?page=" in href and href not in visited:
                pending.append(href)
            elif source == "joboko" and "/tim-viec-lam-lap-trinh-vien?p=" in href:
                pending.append(href)
        print(json.dumps(dict(list_url=url, discovered_jobs=len(links))), flush=True)
    records = []
    for index, url in enumerate(sorted(links)[:150]):
        if blocked:
            break
        soup = get(url)
        if soup is None:
            break
        for script in soup.find_all("script", type="application/ld+json"):
            item = json.loads(script.get_text())
            if isinstance(item, dict) and item.get("@type") == "JobPosting":
                records.append(
                    dict(
                        url=url,
                        captured_at=datetime.now(timezone.utc).isoformat(),
                        html_sha256=hashlib.sha256(
                            (
                                cache / (hashlib.sha256(url.encode()).hexdigest() + ".html")
                            ).read_bytes()
                        ).hexdigest(),
                        job_posting=item,
                    )
                )
        if index % 20 == 0:
            print(json.dumps(dict(fetched=index + 1, records=len(records))), flush=True)
    path = folder / "job_postings.jsonl"
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records))
    (folder / "manifest.json").write_text(
        json.dumps(
            dict(
                created_utc=datetime.now(timezone.utc).isoformat(),
                source=source + " public JobPosting JSON-LD",
                records=len(records),
                list_pages=sorted(visited),
                requests=requests_log,
                access_blocked=blocked,
                file=dict(
                    path=str(path.relative_to(ROOT)),
                    sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                ),
                code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                license_note=(
                    "Public metadata, no explicit open dataset license. "
                    "Raw descriptions stay local; "
                    "source links and derived evidence retained for coursework audit."
                ),
            ),
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )
    print("Completed", len(records), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source", choices=["careerlink_topdev", "joboko"], default="careerlink_topdev"
    )
    collect(parser.parse_args().source)
