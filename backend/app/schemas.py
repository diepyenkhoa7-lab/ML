"""Public request/response contracts for the local analysis application."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

FIELDS = (
    "title",
    "role",
    "level",
    "experience_years",
    "location",
    "skills",
    "salary",
    "posted_date",
    "description",
)


class AnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dataset_id: str = Field(pattern=r"^[a-f0-9]{32}$")
    mapping: dict[str, str] = Field(default_factory=dict)
    currency: Literal["VND", "USD", "EUR"] | None = None
    period: Literal["month", "year"] | None = None
    salary_scale: Literal[1, 1000000] = 1
    use_gemma: bool = False

    @field_validator("mapping")
    @classmethod
    def check_mapping(cls, value):
        if set(value) - set(FIELDS):
            raise ValueError("Tên trường ghép cột không được hỗ trợ")
        columns = [v for v in value.values() if v]
        if len(columns) != len(set(columns)):
            raise ValueError("Một cột nguồn không thể ghép vào hai trường")
        return {k: v for k, v in value.items() if v}


class Preview(BaseModel):
    dataset_id: str
    filename: str
    row_count: int
    columns: list[str]
    preview: list[dict[str, Any]]
    suggested_mapping: dict[str, str]
    provenance: str


class JobState(BaseModel):
    id: str = Field(pattern=r"^[a-f0-9]{32}$")
    status: Literal["queued", "running", "completed", "failed"]
    stage: str
    progress: int = Field(default=0, ge=0, le=100)
    error: str | None = None
    result: dict[str, Any] | None = None


class Profile(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: str = Field(min_length=1, max_length=100)
    level: str = Field(default="Unknown", max_length=100)
    experience_years: float | None = Field(default=None, ge=0, le=80)
    location: str = Field(default="", max_length=200)
    skills: list[str] = Field(default_factory=list, max_length=100)

    @field_validator("skills")
    @classmethod
    def bounded_skills(cls, value):
        if any(len(s) > 200 for s in value):
            raise ValueError("Tên kỹ năng quá dài")
        return value


class ProfileResult(BaseModel):
    profile: dict[str, Any]
    predictions: dict[str, float]
    selected_model: str
    warnings: list[str]
    recommendations: list[dict[str, Any]]
    explanation: str
    evidence: dict[str, Any]


class Meta(BaseModel):
    salary_model: dict[str, Any]
    gemma: dict[str, Any]
    fields: list[str]
    limits: dict[str, int]
