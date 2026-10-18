"""AI-assisted evidence review of the frozen 214-row queue; never call it human gold."""

import json
import re
import sys
from collections import Counter
from pathlib import Path

import pandas as pd
from sklearn.model_selection import GroupShuffleSplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app.services.charts import TECHNOLOGIES  # noqa: E402
from backend.app.services.contracts import digest  # noqa: E402
from scripts.clean_data import checksum  # noqa: E402
from scripts.data_cleaning import SKILL_ALIASES, classify_role, fold, normalize_location, text  # noqa: E402
from scripts.prepare_gemma_sft import SYSTEM, validate_label  # noqa: E402
from scripts.prepare_salary_v31 import company_key  # noqa: E402

VERSION = "2.0.0"
REJECTED = {
    164804: "PLC/HMI and industrial electrical control, not a software developer posting",
    22401: "NX/CNC milling and operating machines",
    331517: "Mechanical CAD/Jig/CNC machining",
    34289: "Power Mill/Master CAM/CNC manufacturing",
    36105: "Sheet-metal punching machine production",
    473318: "BMS/ELV electrical installation and construction supervision",
    47474: "Plastic mold/mechanical design and tooling",
    481896: "Operating and programming laser cutting machines",
    589853: "Mechanical maintenance/CNC fabrication",
    42518: "Fashion product development, not software",
    25490: "Audiovisual installation/PLC field technician; mixed scope",
    24672: "Bank department management across multiple functions; not a single supported role",
    16384: "Combined developer/architect vacancy; single supported role is ambiguous",
}
# Explicit technology strings only. Longest matching spans win; no inferred prerequisites.
CANONICAL = {
    **{k: v for k, v in SKILL_ALIASES.items()},
    **dict(
        zip(
            [
                "api",
                "restful api",
                "restful apis",
                "rest api",
                "nosql",
                "redis",
                "oracle",
                "express",
                "express.js",
                "flutter",
                "android",
                "ios",
                "kotlin",
                "dart",
                "unity",
                "pytorch",
                "tensorflow",
                "laravel",
                "symfony",
                "jquery",
                "bootstrap",
                "azure",
                "elasticsearch",
                "kafka",
                "spring",
                "spring framework",
                "spring boot",
                ".net core",
                ".netcore",
                "asp.net core",
                "nestjs",
                "nest.js",
                "next.js",
                "nlp",
                "machine learning",
                "objective-c",
                "objective c",
                "go",
                "golang",
                "r",
                "c",
                "javascript",
                "java script",
            ],
            [
                "API",
                "REST API",
                "REST API",
                "REST API",
                "NoSQL",
                "Redis",
                "Oracle",
                "Express",
                "Express",
                "Flutter",
                "Android",
                "iOS",
                "Kotlin",
                "Dart",
                "Unity",
                "PyTorch",
                "TensorFlow",
                "Laravel",
                "Symfony",
                "jQuery",
                "Bootstrap",
                "Azure",
                "Elasticsearch",
                "Kafka",
                "Spring",
                "Spring",
                "Spring Boot",
                ".NET Core",
                ".NET Core",
                "ASP.NET Core",
                "NestJS",
                "NestJS",
                "Next.js",
                "NLP",
                "Machine Learning",
                "Objective-C",
                "Objective-C",
                "Go",
                "Go",
                "R",
                "C",
                "JavaScript",
                "JavaScript",
            ],
            strict=True,
        )
    ),
}
for name in [
    "GraphQL",
    "WordPress",
    "Shopify",
    "GitHub",
    "GitLab",
    "CI/CD",
    "SSH",
    "WebSocket",
    "WebSockets",
    "gRPC",
    "RabbitMQ",
    "BullMQ",
    "PM2",
    "WinForms",
    "WPF",
    "WinUI",
    "Entity Framework",
    "Entity Framework Core",
    "PL/SQL",
    "IIS",
    "Apache",
    "Tomcat",
    "WebLogic",
    "SharePoint",
    "XML",
    "XPath",
    "Ajax",
    "JSON",
    "J2EE",
    "Computer Vision",
    "LLM",
    "OpenCV",
    "NumPy",
    "Pandas",
    "Matplotlib",
    "Scikit-learn",
    "CodeIgniter",
    "jQuery",
    "ASP.NET MVC",
    ".NET MVC",
    "MVP",
    "MVVM",
    "OOP",
    "JWT",
    "OAuth",
    "Firebase",
    "Figma",
    "Selenium",
    "Jenkins",
    "Jest",
    "Mocha",
    "Cocos",
    "Cocos2d",
]:
    CANONICAL[name.casefold()] = name
CANONICAL["websockets"] = "WebSocket"
for name in TECHNOLOGIES:
    CANONICAL.setdefault(name.casefold(), name)


def grounded_skills(content):
    matches = []
    for alias, canonical in CANONICAL.items():
        flags = 0 if alias in {"c", "r", "go"} else re.I
        literal = {"c": "C", "r": "R", "go": "Go"}.get(alias, alias)
        pattern = r"(?<![\w])" + re.escape(literal) + r"(?![\w+#&])"
        for match in re.finditer(pattern, content, flags):
            matches.append((match.start(), match.end(), canonical, match.group()))
    occupied, evidence = set(), {}
    for start, end, name, span in sorted(matches, key=lambda m: (-(m[1] - m[0]), m[0])):
        positions = set(range(start, end))
        if not positions & occupied:
            evidence.setdefault(name, span)
            occupied.update(positions)
    return sorted(evidence, key=str.casefold), evidence


def explicit_experience(content):
    source = fold(content)
    zero = re.search(r"khong (?:yeu cau|can) kinh nghiem|no experience required", source)
    patterns = [
        r"(?<!\d)(\d{1,2}(?:[.,]\d+)?)(?:\s*[-–]\s*\d{1,2})?\s*"
        r"(nam|years?|thang|months?)\s*(?:kinh nghiem|(?:of\s+)?experience)",
        r"kinh nghiem[^\d.;:]{0,25}(\d{1,2}(?:[.,]\d+)?)"
        r"(?:\s*[-–]\s*\d{1,2})?\s*(nam|thang)",
    ]
    evidence = []
    for pattern in patterns:
        for match in re.finditer(pattern, source):
            value = float(match.group(1).replace(",", "."))
            if match.group(2) in {"thang", "month", "months"}:
                value /= 12
            if 0 <= value <= 40:
                evidence.append((value, match.group()))
    values = {v for v, _ in evidence}
    if zero:
        values.add(0.0)
        evidence.append((0.0, zero.group()))
    return (next(iter(values)) if len(values) == 1 else None), evidence


def extraction_role(title):
    value = fold(title)
    if re.search(r"full[ -]?stack", value):
        return "Full-stack Developer"
    if re.search(r"\b(?:ai|ml) engineer|ky su (?:lap trinh )?ai\b|machine learning", value):
        return "ML Engineer"
    if re.search(r"embedded|firmware|nhung|vi dieu khien", value):
        return "Embedded Engineer"
    if re.search(r"android|\bios\b|flutter|react native|mobile", value):
        return (
            "Mobile Developer"
            if not re.search(r"\bweb\b|front.?end", value)
            else "Software Developer"
        )
    if re.search(r"front.?end", value) and re.search(r"back.?end", value):
        return "Software Developer"
    if re.search(r"\bfe\b", value):
        return "Frontend Developer"
    return classify_role(title)["role"]


def location_label(raw):
    content = fold(raw)
    cities = [
        name
        for name, pattern in [
            ("Hà Nội", r"ha noi|hanoi"),
            ("TP.HCM", r"ho chi minh|\bhcm\b|sai gon"),
            ("Đà Nẵng", r"da nang|danang"),
        ]
        if re.search(pattern, content)
    ]
    if len(cities) == 1:
        return cities[0]
    return None if len(cities) > 1 else normalize_location(raw)["location"]


def review():
    from transformers import AutoTokenizer

    output = ROOT / f"data/annotation/gemma_v{VERSION}"
    corpus = ROOT / f"data/finetune_reviewed/v{VERSION}"
    if output.exists() or corpus.exists():
        raise ValueError("Preserve frozen review/corpus; select a new version")
    source = ROOT / "data/annotation/v3.1.0/salary_review_queue.jsonl"
    previous = json.loads((source.parent / "manifest.json").read_text())
    assert checksum(source) == previous["files"][source.name]
    queue = [json.loads(line) for line in source.read_text().splitlines()]
    assert len(queue) == 214
    raw_path = ROOT / "data/raw/tinixai_2026/data.parquet"
    origin = json.loads((raw_path.parent / "manifest.json").read_text())
    assert checksum(raw_path) == origin["files"]["data.parquet"]["sha256"]
    frame = pd.read_parquet(raw_path)
    ids = {int(row["record_id"].split(":")[1]) for row in queue}
    frame = frame[frame.id.isin(ids)].set_index("id")
    frozen = pd.concat(
        [
            pd.read_csv(ROOT / f"data/splits/v3.1.0/vn_developer/{part}.csv")
            for part in ["train", "older_train"]
        ]
    ).set_index("record_id")
    tokenizer = AutoTokenizer.from_pretrained(ROOT / "models/gemma-mlx-4bit", local_files_only=True)
    reviewed, examples, seen = [], [], set()
    for queued in queue:
        rid = queued["record_id"]
        number = int(rid.split(":")[1])
        raw = frame.loc[number].to_dict()
        title, requirements = text(raw["job_title"]), text(raw["requirements"])
        if requirements in {"-", "None", "nan"}:
            requirements = ""
        label = frozen.loc[rid]
        record = dict(
            source_record_id=rid,
            reviewer="Codex AI assisted source-evidence review",
            review_method="all-record checks + title review + targeted original-text adjudication",
            quality="ai_reviewed_silver_not_human_gold",
            gold=None,
            original_queue_sha256=checksum(source),
            raw_record_sha256=digest({k: text(v) for k, v in raw.items()}),
            proposed=queued["proposed"],
        )
        if number in REJECTED:
            record.update(status="rejected", reason=REJECTED[number], reviewed_label=None)
            reviewed.append(record)
            continue
        evidence = text(label.period_evidence)
        # Include source evidence, not the derived midpoint or a list of predicted skills.
        prefix = ["Phiếu tin tuyển dụng từ dữ liệu đã thu thập:", f"Chức danh: {title}"]
        prefix += ["Địa điểm: " + text(raw["location"])]
        prefix += ["Lương nguồn: " + text(raw["salary"]), "Chi tiết lương nguồn: " + evidence]
        # Context budgeting chooses whole source sentences; labels refer only to visible evidence.
        sentences = re.split(r"(?<=[.;。])\s+|\n|\s+[•·]\s*", requirements)
        visible = []
        for sentence in sentences:
            if not sentence.strip():
                continue
            candidate = " ".join(visible + [sentence])
            messages = [
                dict(role="system", content=SYSTEM),
                dict(
                    role="user",
                    content="\n".join(prefix + ["Yêu cầu trích nguyên văn: " + candidate]),
                ),
            ]
            # Reserve 256 tokens for the answer, matching the web worker's 1024-token contract.
            length = len(
                tokenizer.apply_chat_template(
                    messages, add_generation_prompt=True, return_dict=False
                )
            )
            if length + 256 <= 1024:
                visible.append(sentence)
        content = "\n".join(prefix + ["Yêu cầu trích nguyên văn: " + " ".join(visible)])
        exp, exp_evidence = explicit_experience(title + " " + " ".join(visible))
        if number == 4622 and any(value == 2 for value, _ in exp_evidence):
            # Adjudicated source: two years overall; one year applies to each sub-specialism.
            exp = 2.0
        skills, skill_evidence = grounded_skills(title + " " + " ".join(visible))
        role = extraction_role(title)
        target = dict(
            role=role,
            location=location_label(raw["location"]),
            experience_years=exp,
            skills=skills if skills or visible else None,
            salary_min=float(label.salary_min),
            salary_max=float(label.salary_max),
            currency="VND",
            salary_period="month",
        )
        validate_label(target)
        record.update(
            status="accepted",
            reviewed_label=target,
            evidence=dict(
                salary=evidence,
                experience=exp_evidence,
                skills=skill_evidence,
                location=text(raw["location"]),
                role=title,
            ),
            notes=[
                "Experience metadata is not model input or ground truth; use visible job text only",
                "Only exact visible technology spans labelled; missing evidence stays null",
                "Whole source sentences selected explicitly; no hidden label-preserving truncation",
            ],
            visible_requirements=" ".join(visible),
            source_requirements_chars=len(requirements),
            changes={
                k: dict(before=queued["proposed"].get(k), after=v)
                for k, v in target.items()
                if queued["proposed"].get(k) != v
            },
        )
        content_key = digest(
            [fold(title), company_key(raw["company_name"]), fold(" ".join(visible)), target]
        )
        if content_key in seen:
            record.update(
                status="duplicate_excluded", reason="same company/title/visible evidence/target"
            )
        else:
            seen.add(content_key)
            messages = [
                dict(role="system", content=SYSTEM),
                dict(role="user", content=content),
                dict(role="assistant", content=json.dumps(target, ensure_ascii=False)),
            ]
            tokens = tokenizer.apply_chat_template(messages, return_dict=False)
            prompt = tokenizer.apply_chat_template(
                messages[:-1], add_generation_prompt=True, return_dict=False
            )
            assert tokens[: len(prompt)] == prompt
            if len(tokens) > 1024 or len(tokens) - len(prompt) > 256:
                record.update(status="length_excluded", reason="No truncation of assistant target")
            else:
                examples.append(
                    dict(
                        source_record_id=rid,
                        group_id=digest(company_key(raw["company_name"])),
                        company_key=company_key(raw["company_name"]),
                        source_year=int(raw["year"]),
                        source_dataset="tinixai_reviewed",
                        variant="source_text_extract",
                        label_quality="ai_reviewed_silver_not_human_gold",
                        task="job_card_extraction",
                        messages=messages,
                        tokens=len(tokens),
                        prompt_tokens=len(prompt),
                    )
                )
        reviewed.append(record)
    old = ROOT / "data/finetune_full/v1.0.0"
    parent_manifest = json.loads((old / "manifest.json").read_text())
    assert checksum(old / "train.jsonl") == parent_manifest["splits"]["train"]["sha256"]
    replay = [json.loads(line) for line in (old / "train.jsonl").read_text().splitlines()]
    old_candidates = pd.read_csv(
        ROOT / "data/processed/reviewed/v1.0.1/all_candidates.csv", low_memory=False
    )
    old_train_ids = {r["source_record_id"] for r in replay}
    old_train_companies = {
        company_key(c)
        for c in old_candidates[old_candidates.record_id.isin(old_train_ids)].company
        if text(c)
    }
    eligible = pd.DataFrame(
        [
            dict(index=i, group=r["group_id"])
            for i, r in enumerate(examples)
            if r["company_key"] not in old_train_companies
        ]
    )
    dev_idx, test_idx = next(
        GroupShuffleSplit(test_size=0.15, random_state=20261018).split(
            eligible, groups=eligible.group
        )
    )
    dev, test = eligible.iloc[dev_idx], eligible.iloc[test_idx]
    _, valid_idx = next(
        GroupShuffleSplit(test_size=0.1765, random_state=20261018).split(dev, groups=dev.group)
    )
    valid = dev.iloc[valid_idx]
    held = dict(valid=set(valid.group), test=set(test.group))
    parts = dict(train=list(replay), valid=[], test=[])
    for row in examples:
        split = (
            "valid"
            if row["group_id"] in held["valid"]
            else "test"
            if row["group_id"] in held["test"]
            else "train"
        )
        row["split"] = split
        parts[split].append(row)
    assert len(held["valid"] & held["test"]) == 0
    assert all(
        r["company_key"] not in old_train_companies for s in ["valid", "test"] for r in parts[s]
    )
    output.mkdir(parents=True)
    corpus.mkdir(parents=True)
    ledger = output / "review.jsonl"
    ledger.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in reviewed))
    manifest = dict(
        version=VERSION,
        quality="ai_reviewed_silver_not_human_gold",
        total_reviewed=len(reviewed),
        status_counts=dict(Counter(r["status"] for r in reviewed)),
        source_queue_sha256=checksum(source),
        review_sha256=checksum(ledger),
        code_sha256=checksum(Path(__file__)),
        human_gold_rows=0,
    )
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    splits = {}
    for split, rows in parts.items():
        for row in rows:
            row["split"] = split
        path = corpus / f"{split}.jsonl"
        path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
        splits[split] = dict(
            examples=len(rows),
            source_records=len({r["source_record_id"] for r in rows}),
            groups=len({r["group_id"] for r in rows}),
            max_tokens=max(r["tokens"] for r in rows),
            sha256=checksum(path),
        )
    corpus_manifest = dict(
        version=VERSION,
        quality=manifest["quality"],
        task="job_card_extraction",
        max_seq_length=1024,
        splits=splits,
        system_prompt=SYSTEM,
        review_manifest_sha256=checksum(output / "manifest.json"),
        parent_corpus_manifest_sha256=checksum(old / "manifest.json"),
        replay_train_examples=len(replay),
        new_examples=len(examples),
        split_policy=(
            "company-group seed20261018; new valid/test exclude parent training companies; "
            "old test never reused"
        ),
        builder_sha256=checksum(Path(__file__)),
        limits=[
            "AI-reviewed silver, not human gold",
            "Extracted source sentences, not entire long ads",
            "Experience metadata intentionally not input",
            "Salary extraction, not salary regression",
        ],
    )
    (corpus / "manifest.json").write_text(
        json.dumps(corpus_manifest, ensure_ascii=False, indent=2) + "\n"
    )
    print(json.dumps(dict(review=manifest, corpus=corpus_manifest), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    review()
