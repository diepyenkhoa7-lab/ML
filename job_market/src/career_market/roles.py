"""Conservative occupational evidence for the seven agreed software roles."""

import re

ROLE_PATTERNS = {
    "Backend": r"\bback[ -]?end\b",
    "Frontend": r"\bfront[ -]?end\b",
    "Fullstack": r"\bfull[ -]?stack\b",
    "Mobile": r"\b(?:mobile|android|ios|flutter)\b",
    "Data/ML": r"\b(?:data\s*/\s*ml|data (?:engineer|scientist|analyst)|machine learning(?: developer| engineer)?|ml engineer|ai (?:developer|engineer|researcher)|lập trình viên ai)\b",
    "DevOps": r"\b(?:devops|sre|site reliability engineer)\b",
    "QA Automation": r"\b(?:automation test(?:er|ing)?|test automation|qa automation|kiểm thử tự động|software tester.{0,25}automation)\b",
}
ACTION = r"\b(?:build|develop|design|implement|maintain|xây dựng|phát triển|thiết kế|bảo trì)\b"
TASK_PATTERNS = {
    "Backend": r"\b(?:back[ -]?end|rest(?:ful)? apis?|server[- ]side|dịch vụ máy chủ)\b",
    "Frontend": r"\b(?:front[ -]?end|user interfaces?|giao diện web)\b",
    "Fullstack": ROLE_PATTERNS["Fullstack"],
    "Mobile": ROLE_PATTERNS["Mobile"],
}


def classify_role(title: str, description: str = "", requirements: str = "") -> dict:
    excluded = re.search(
        r"\b(?:cnc|plc|hardware|knitwear|phần cứng|dệt kim|marketing|sales|"
        r"customer service|chăm sóc khách hàng|kinh doanh|bán hàng)\b",
        title,
        re.I,
    )
    if excluded:
        return {
            "role": None,
            "role_status": "out_of_scope",
            "role_evidence": [{"field": "title", "text": excluded.group()}],
            "role_reason": "Chức danh thuộc nghề ngoài phạm vi bảy vai trò phần mềm.",
        }
    evidence = []
    candidates = set()
    for role, pattern in ROLE_PATTERNS.items():
        match = re.search(pattern, title, re.IGNORECASE)
        if match:
            candidates.add(role)
            evidence.append({"field": "title", "text": match.group()})
    tasks = re.split(
        r"(?im)^\s*(?:requirements|qualifications|skills|yêu cầu(?: công việc)?|kỹ năng)\s*(?:[:：]|$)",
        re.sub(r"<[^>]*>", "\n", description),
        maxsplit=1,
    )[0]
    for sentence in re.split(r"[\n;]+|(?<=[.!?])\s+", tasks):
        action = re.search(ACTION, sentence, re.I)
        if not action or re.search(
            r"\b(?:experience|knowledge|familiar|preferred|plus|kinh nghiệm|hiểu biết|lợi thế)\b",
            sentence,
            re.I,
        ):
            continue
        responsibility = sentence[action.start() :]
        if re.search(
            r"\b(?:marketing|campaigns?|sales|knitwear|cnc|plc|hardware)\b", responsibility, re.I
        ):
            continue
        for role, pattern in TASK_PATTERNS.items():
            if re.search(pattern, responsibility, re.I):
                candidates.add(role)
                item = {"field": "description", "text": sentence}
                if item not in evidence:
                    evidence.append(item)
    if "Fullstack" in candidates and candidates <= {"Fullstack", "Backend", "Frontend"}:
        candidates = {"Fullstack"}
    if candidates:
        role = next(iter(candidates)) if len(candidates) == 1 else None
        return {
            "role": role,
            "role_status": "matched" if role else "review",
            "role_evidence": evidence,
            "role_reason": (
                f"Có bằng chứng cho {role} từ chức danh hoặc nhiệm vụ."
                if role
                else "Có bằng chứng cho nhiều vai trò: " + ", ".join(sorted(candidates)) + "."
            ),
        }
    generic = re.search(r"\b(?:developer|engineer|software|lập trình|phần mềm)\b", title, re.I)
    return {
        "role": None,
        "role_status": "review" if generic else "out_of_scope",
        "role_evidence": [],
        "role_reason": (
            "Chức danh chưa đủ bằng chứng phân biệt bảy vai trò phần mềm."
            if generic
            else "Chưa có bằng chứng thuộc bảy vai trò phần mềm."
        ),
    }
