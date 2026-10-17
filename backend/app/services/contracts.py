"""Strict transport: reject ambiguity instead of repairing model output."""

import hashlib
import json
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from scripts.prepare_gemma_sft import validate_label


def strict_json(value):
    def unique(pairs):
        result = {}
        for key, item in pairs:
            if key in result:
                raise ValueError(f"Khóa JSON bị trùng: {key}")
            result[key] = item
        return result

    def invalid(value):
        raise ValueError(f"JSON không hỗ trợ {value}")

    return json.loads(value, object_pairs_hook=unique, parse_constant=invalid)


def digest(value):
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False).encode()
    ).hexdigest()


class GemmaLabel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)
    role: str | None = Field(max_length=100)
    location: str | None = Field(max_length=200)
    experience_years: float | None = Field(ge=0, le=80)
    skills: list[str] | None = Field(max_length=100)
    salary_min: float | None = Field(ge=0)
    salary_max: float | None = Field(ge=0)
    currency: str | None = Field(max_length=16)
    salary_period: Literal["month", "year"] | None

    @model_validator(mode="before")
    @classmethod
    def check_source(cls, value):
        validate_label(value)
        return value

    @model_validator(mode="after")
    def check_coherence(self):
        if any(len(s) > 200 for s in self.skills or []):
            raise ValueError("Tên kỹ năng quá dài")
        if self.salary_min is None and self.salary_max is None:
            if self.currency is not None or self.salary_period is not None:
                raise ValueError("Không có số tiền thì tiền tệ và kỳ lương phải null")
        return self


class GemmaItem(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    index: int = Field(ge=0, le=19)
    input_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    value: GemmaLabel | None
    raw_output: str | None
    error: str | None

    @model_validator(mode="after")
    def check_outcome(self):
        if (self.value is None) == (self.error is None):
            raise ValueError("Mỗi dòng phải có kết quả hoặc lỗi, không được thiếu/có cả hai")
        if self.value is not None and self.raw_output is None:
            raise ValueError("Thiếu đầu ra gốc của model")
        return self


class GemmaBatch(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    schema_version: Literal["career.gemma.batch.v1"]
    request_id: str = Field(pattern=r"^[a-f0-9]{32}$")
    items: list[GemmaItem] = Field(min_length=1, max_length=20)
    provenance: dict[str, str]

    def check_request(self, request_id, cards):
        if self.request_id != request_id or len(self.items) != len(cards):
            raise ValueError("Gemma trả sai lượt hoặc thiếu/thừa dòng")
        for index, (card, item) in enumerate(zip(cards, self.items, strict=True)):
            if item.index != index or item.input_sha256 != digest(card):
                raise ValueError("Gemma trả sai thứ tự hoặc sai nội dung dòng")
        required = {"adapter", "adapter_sha256", "base_weight_sha256", "system_prompt_sha256"}
        if not required <= self.provenance.keys():
            raise ValueError("Gemma thiếu bằng chứng model đã chạy")
        return self
