from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, HttpUrl, field_validator


class Evidence(BaseModel):
    source_url: HttpUrl
    quoted_evidence: str = Field(min_length=1)
    source_title: str | None = None
    source_type: str = "public_web"
    published_at: datetime | None = None
    retrieved_at: datetime = Field(default_factory=datetime.utcnow)
    identity_match_score: float = Field(ge=0, le=1)
    evidence_score: float = Field(ge=0, le=1)


class Fact(BaseModel):
    field: str
    value: Any | None = None
    normalized_value: str | None = None
    unit: str | None = None
    status: str = "verified"
    confidence: float = Field(ge=0, le=1)
    evidence: list[Evidence] = []
    first_seen_at: datetime = Field(default_factory=datetime.utcnow)
    last_seen_at: datetime = Field(default_factory=datetime.utcnow)
    is_current: bool = True


class CompanyIdentity(BaseModel):
    company_number: str = Field(pattern=r"^\d{9}$")
    legal_name: str | None = None
    status: str | None = None
    address: str | None = None
    postal_code: str | None = None
    city: str | None = None
    country: str = "Norway"
    organization_type: str | None = None
    website: HttpUrl | None = None

    @field_validator("company_number")
    @classmethod
    def normalize_number(cls, value: str) -> str:
        return value.strip().replace(" ", "")


class CompanyProfile(BaseModel):
    company: CompanyIdentity
    facts: list[Fact] = []
    events: list[dict[str, Any]] = []
    verification: dict[str, Any] = {}
    research: dict[str, Any] = {}
