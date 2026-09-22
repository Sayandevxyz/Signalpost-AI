from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class Company:
    company_number: str
    legal_name: str | None = None
    status: str | None = None
    website: str | None = None
    updated_at: datetime | None = None

@dataclass
class CompanyFact:
    company_id: str
    field_name: str
    value_json: Any
    status: str = "verified"
    is_current: bool = True

@dataclass
class EvidenceRecord:
    fact_id: str
    source_url: str
    quoted_evidence: str
    retrieved_at: datetime
