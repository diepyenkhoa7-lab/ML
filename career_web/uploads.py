"""Upload parsing and column mapping; never modifies the frozen dataset."""

import re
import unicodedata
import uuid
import zipfile
from pathlib import Path

from career_ai.data import FEATURES
from career_ai.inputs import read_profiles
from career_auto.state import read, write

from .config import MAX_ROWS, WEB_OUTPUT
from .repository import records

FIELDS = FEATURES + ["description", "salary", "unit"]
ALIASES = {
    "market": ["market", "thi truong"],
    "role": ["role", "job_title", "title", "DevType", "vai tro", "vi tri"],
    "location": ["location", "Country", "region", "city", "khu vuc", "dia diem"],
    "experience_years": ["experience_years", "WorkExp", "years_experience", "kinh nghiem"],
    "skills": ["skills", "technologies", "LanguageHaveWorkedWith", "ky nang"],
    "description": ["description", "requirements", "job_description", "mo ta"],
    "salary": ["salary", "ConvertedCompYearly", "actual_salary", "luong"],
    "unit": ["unit", "salary_unit", "don vi"],
}


def column_key(value):
    text = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", text.lower())


def suggest_mapping(columns):
    normalized = {column_key(c): c for c in columns}
    return {
        key: next((normalized[column_key(a)] for a in names if column_key(a) in normalized), "")
        for key, names in ALIASES.items()
    }


def save_upload(content, filename, folder=None):
    folder = Path(folder or WEB_OUTPUT / "uploads")
    suffix = Path(filename or "").suffix.lower()
    if suffix not in [".csv", ".xlsx", ".json"]:
        raise ValueError("Chỉ nhận file CSV, XLSX hoặc JSON.")
    if not content:
        raise ValueError("File đang rỗng.")
    folder.mkdir(parents=True, exist_ok=True)
    identifier = uuid.uuid4().hex
    path = folder / (identifier + suffix)
    path.write_bytes(content)
    try:
        if suffix == ".xlsx":
            with zipfile.ZipFile(path) as archive:
                if sum(i.file_size for i in archive.infolist()) > 80 * 1024 * 1024:
                    raise ValueError("Bảng tính sau giải nén quá lớn (tối đa80MB).")
        frame = read_profiles(path)
        frame.columns = frame.columns.map(str)
        if frame.empty:
            raise ValueError("Không có dòng dữ liệu trong file.")
        if len(frame) > MAX_ROWS:
            raise ValueError(
                f"File có {len(frame)} dòng. Mỗi lần tối đa{MAX_ROWS} dòng; hãy chia file."
            )
        info = dict(
            id=identifier,
            filename=Path(filename).name,
            rows=len(frame),
            columns=list(frame.columns),
            mapping=suggest_mapping(frame.columns),
            preview=records(frame.head(5)),
            records=records(frame),
        )
        write(folder / (identifier + ".meta.json"), info)
        return {k: v for k, v in info.items() if k != "records"}
    except Exception:
        path.unlink(missing_ok=True)
        raise


def mapped_rows(request, folder=None):
    folder = Path(folder or WEB_OUTPUT / "uploads")
    path = folder / (request.upload_id + ".meta.json")
    if not path.exists():
        raise FileNotFoundError("Không tìm thấy file đã tải lên; hãy tải lại.")
    info = read(path)
    if set(request.mapping) - set(FIELDS):
        raise ValueError("Có trường ánh xạ không được hỗ trợ.")
    columns = [v for v in request.mapping.values() if v]
    if any(c not in info["columns"] for c in columns) or len(columns) != len(set(columns)):
        raise ValueError("Ánh xạ cột không hợp lệ hoặc dùng trùng cột.")
    if not request.mapping.get("description") and not all(
        request.mapping.get(k) for k in ["role", "experience_years", "skills"]
    ):
        raise ValueError("Cần cột vai trò, kinh nghiệm, kỹ năng; hoặc cột mô tả để AI trích xuất.")
    rows = []
    for row in info["records"]:
        item = {k: row.get(c) for k, c in request.mapping.items() if c}
        if item.get("market") in [None, ""]:
            item["market"] = request.market
        if item.get("location") in [None, ""]:
            item["location"] = request.location
        if item.get("unit") in [None, ""]:
            item["unit"] = request.reference_unit
        rows.append(item)
    return info["filename"], rows


def export_frame(frame):
    """Keep user text literal when opened in spreadsheet software."""
    result = frame.copy()
    for column in result:
        result[column] = result[column].map(
            lambda v: (
                "'" + v if isinstance(v, str) and v.lstrip().startswith(("=", "+", "-", "@")) else v
            )
        )
    return result
