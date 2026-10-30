from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

Market = Literal["vietnam", "international"]


class AnalysisRequest(BaseModel):
    upload_id: str = Field(pattern=r"^[a-f0-9]{32}$")
    mapping: dict[str, str]
    market: Market
    location: str = Field(default="", max_length=200)
    reference_unit: Literal["", "USD/year", "VND/month"] = ""
    include_advice: bool = False


class ProfileRequest(BaseModel):
    market: Market
    role: str | None = Field(default=None, max_length=200)
    location: str = Field(min_length=1, max_length=200)
    experience_years: float | None = Field(default=None, ge=0, le=80, allow_inf_nan=False)
    skills: str | list[str] | None = None
    description: str = Field(default="", max_length=12000)
    include_advice: bool = True

    @field_validator("experience_years", mode="before")
    @classmethod
    def reject_boolean(cls, value: Any):
        if isinstance(value, bool):
            raise ValueError("Kinh nghiệm phải là số năm")
        return value

    @field_validator("skills")
    @classmethod
    def bounded_skills(cls, value):
        if value is not None and len(str(value)) > 6000:
            raise ValueError("Danh sách kỹ năng quá dài")
        return value
