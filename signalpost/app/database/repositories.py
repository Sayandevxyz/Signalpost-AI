from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from .models import Company, CompanyFact, EvidenceRecord, ResearchRun


def get_company(db: Session, company_number: str) -> Company | None:
    return db.scalar(select(Company).where(Company.company_number == company_number).options(selectinload(Company.facts)))


def upsert_company(db: Session, data: dict[str, Any]) -> Company:
    number = data["company_number"]
    company = db.scalar(select(Company).where(Company.company_number == number))
    if company is None:
        company = Company(company_number=number)
        db.add(company)
    for field in ("legal_name", "organization_type", "status", "address", "postal_code", "city", "country", "website", "industry", "description"):
        if field in data and data[field] is not None:
            setattr(company, field, data[field])
    company.last_researched_at = datetime.now(UTC)
    db.commit()
    db.refresh(company)
    return company


def add_fact(db: Session, company: Company, data: dict[str, Any]) -> CompanyFact:
    fact = CompanyFact(
        company_id=company.id,
        field_name=data["field_name"],
        value_json=data.get("value_json"),
        normalized_value=data.get("normalized_value"),
        unit=data.get("unit"),
        status=data.get("status", "verified"),
        confidence=data.get("confidence"),
    )
    db.add(fact)
    db.commit()
    db.refresh(fact)
    return fact


def add_evidence(db: Session, fact: CompanyFact, data: dict[str, Any]) -> EvidenceRecord:
    evidence = EvidenceRecord(fact_id=fact.id, **data)
    db.add(evidence)
    db.commit()
    db.refresh(evidence)
    return evidence


def start_run(db: Session, company: Company | None = None) -> ResearchRun:
    run = ResearchRun(company_id=company.id if company else None)
    db.add(run)
    db.commit()
    db.refresh(run)
    return run
