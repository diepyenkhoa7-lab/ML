"""Bounded table import and shared deterministic normalization; no fitted transforms."""

import csv
import io
import json
import re
import zipfile
from pathlib import Path

import pandas as pd

from scripts.data_cleaning import (
    classify_role,
    fold,
    level,
    native_salary,
    normalize_location,
    normalize_skills,
    numeric,
    parse_experience,
    parse_salary,
    text,
)

ROOT = Path(__file__).resolve().parents[3]
MAX_BYTES, MAX_ROWS, MAX_COLUMNS = 10 * 1024 * 1024, 2000, 100
ALIASES = {
    "role": ["role", "vai tro", "vi tri", "job_role"],
    "title": ["title", "job_title", "chuc danh", "ten cong viec", "position"],
    "level": ["level", "seniority", "cap bac", "job_level"],
    "experience_years": ["experience_years", "experience", "kinh nghiem", "years_experience"],
    "location": ["location", "location_raw", "city", "khu vuc", "dia diem"],
    "skills": ["skills", "skills_json", "skills_raw", "ky nang", "technologies"],
    "salary": ["salary_monthly_vnd", "salary", "salary_raw", "luong", "muc luong"],
    "description": ["description", "job_description", "mo ta", "noi dung"],
    "posted_date": ["posted_date", "posting_date", "date_posted", "ngay dang"],
}


def json_safe(value):
    # pandas handles NA, timestamps and numpy scalars consistently.
    return json.loads(
        pd.DataFrame(value).to_json(orient="records", date_format="iso", force_ascii=False)
    )


def read_table(content: bytes, filename: str):
    if not content or len(content) > MAX_BYTES:
        raise ValueError("File trống hoặc vượt giới hạn 10 MiB")
    suffix = Path(filename).suffix.lower()
    try:
        if suffix == ".csv":
            try:
                decoded = content.decode("utf-8-sig")
            except UnicodeDecodeError:
                decoded = content.decode("cp1258")
            try:
                separator = csv.Sniffer().sniff(decoded[:8192], delimiters=",;\t|").delimiter
            except csv.Error:
                separator = ","
            header = next(csv.reader(io.StringIO(decoded), delimiter=separator))
            if len(header) != len(set(header)):
                raise ValueError("Tên cột bị trùng")
            frame = pd.read_csv(io.StringIO(decoded), sep=separator, nrows=MAX_ROWS + 1)
        elif suffix == ".xlsx":
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                if sum(x.file_size for x in archive.infolist()) > 50 * 1024 * 1024:
                    raise ValueError("XLSX giải nén vượt 50 MiB")
            frame = pd.read_excel(io.BytesIO(content), engine="openpyxl", nrows=MAX_ROWS + 1)
        elif suffix == ".json":
            value = json.loads(content)
            if not isinstance(value, list) or any(not isinstance(row, dict) for row in value):
                raise ValueError("JSON phải là danh sách object, mỗi object là một dòng")
            if any(isinstance(cell, dict) for row in value for cell in row.values()):
                raise ValueError("Không hỗ trợ object lồng trong ô dữ liệu")
            frame = pd.DataFrame(value)
        else:
            raise ValueError("Chỉ nhận CSV, XLSX hoặc JSON; không nhận file model")
    except (UnicodeError, pd.errors.ParserError, zipfile.BadZipFile, KeyError) as exc:
        raise ValueError("Không đọc được bảng dữ liệu; kiểm tra định dạng và encoding") from exc
    if frame.empty or len(frame) > MAX_ROWS or len(frame.columns) > MAX_COLUMNS:
        raise ValueError("Bảng cần 1–2.000 dòng và tối đa 100 cột")
    columns = [str(c).strip() for c in frame.columns]
    if any(not c or len(c) > 200 for c in columns) or len(set(columns)) != len(columns):
        raise ValueError("Tên cột rỗng, trùng hoặc quá dài")
    frame.columns = columns
    rows = json_safe(frame)
    if any(len(str(cell)) > 20000 for row in rows for cell in row.values() if cell is not None):
        raise ValueError("Một ô dữ liệu vượt 20.000 ký tự")
    return rows


def suggest_mapping(columns):
    normalized = {fold(c).replace("-", "_"): c for c in columns}
    selected = {}
    for target, aliases in ALIASES.items():
        for alias in aliases:
            if alias in normalized and normalized[alias] not in selected.values():
                selected[target] = normalized[alias]
                break
    return selected


def skills_from(value):
    if isinstance(value, list):
        if any(not isinstance(item, str) for item in value):
            raise ValueError("Kỹ năng phải là danh sách chuỗi")
        raw = json.dumps(value, ensure_ascii=False)
    else:
        raw = text(value)
    if not raw:
        return []
    parsed = normalize_skills(raw)
    if not parsed["valid"]:
        parsed = normalize_skills(re.sub(r"[,|\n]", ";", raw), separator=";")
    if not parsed["valid"]:
        raise ValueError("Danh sách kỹ năng không hợp lệ")
    return parsed["skills"]


def normalize_row(raw, mapping, options, extracted=None):
    def get(key):
        return raw.get(mapping.get(key, ""))

    extracted = extracted or {}
    warnings, errors = [], []
    if any(isinstance(get(key), (list, dict)) for key in mapping if key != "skills"):
        raise ValueError("Chỉ cột kỹ năng được chứa danh sách; các trường khác cần giá trị đơn")
    title = text(get("title"))
    role_raw = text(get("role"))
    role = role_raw or classify_role(title)["role"] or extracted.get("role")
    if role:
        role = classify_role(role)["role"] or role
    experience_raw = get("experience_years")
    experience = None
    if text(experience_raw):
        experience = numeric(experience_raw)
        if experience is None:
            experience = parse_experience(experience_raw)["experience_years"]
        if experience is None or not 0 <= experience <= 80:
            errors.append("Kinh nghiệm không hợp lệ; nhập số năm hoặc chuỗi có năm/tháng")
    else:
        experience = extracted.get("experience_years")
    skills = skills_from(get("skills")) or skills_from(extracted.get("skills"))
    location = normalize_location(get("location") or extracted.get("location"))["location"]
    seniority = level(get("level"), title) or "Unknown"
    if not role:
        errors.append("Thiếu vai trò; ghép cột chức danh/vai trò hoặc bật Gemma cho mô tả")
    if experience is None:
        warnings.append("Thiếu kinh nghiệm: pipeline dùng giá trị điền từ train")
    if not location:
        warnings.append("Thiếu khu vực")
    if not skills:
        warnings.append("Thiếu kỹ năng")
    actual, salary_status = None, "missing"
    salary_raw = get("salary")
    if text(salary_raw):
        if isinstance(salary_raw, bool):
            parsed = native_salary(None, None, None, None)
        elif mapping.get("salary") == "salary_monthly_vnd":
            amount = numeric(salary_raw)
            parsed = native_salary(amount, amount, "VND", "month")
        elif numeric(salary_raw) is not None:
            amount = numeric(salary_raw) * options.salary_scale
            parsed = native_salary(amount, amount, options.currency, options.period)
        else:
            parsed = parse_salary(salary_raw, default_period=options.period)
            if parsed["status"] == "currency_unknown" and options.currency:
                parsed = native_salary(
                    parsed["salary_min"],
                    parsed["salary_max"],
                    options.currency,
                    parsed["salary_period"],
                )
        actual, salary_status = parsed["salary_monthly_vnd"], parsed["status"]
        if actual is None:
            warnings.append(
                "Không dùng lương làm nhãn: thiếu/sai kỳ, tiền tệ, khoảng hoặc không phải VND"
            )
    posted = None
    if text(get("posted_date")):
        date_value = text(get("posted_date"))
        date_format = (
            "%d/%m/%Y" if re.fullmatch(r"\d{1,2}/\d{1,2}/\d{4}", date_value) else "ISO8601"
        )
        parsed_date = pd.to_datetime(date_value, format=date_format, errors="coerce", utc=True)
        if not pd.isna(parsed_date):
            posted = parsed_date.date().isoformat()
        else:
            warnings.append("Ngày đăng không hợp lệ")
    return dict(
        role=role,
        level=seniority,
        location=location,
        experience_years=experience,
        skills=skills,
        salary_monthly_vnd=actual,
        salary_status=salary_status,
        posted_date=posted,
        warnings=warnings,
        errors=errors,
        extraction=extracted or None,
    )
