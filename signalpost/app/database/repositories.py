from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
from typing import Any
from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from .models import Company, CompanyEvent, CompanyFact, EvidenceRecord, ResearchRun


def get_company(db: Session, company_number: str) -> Company | None:
    return db.scalar(
        select(Company)
        .where(Company.company_number == company_number)
        .options(selectinload(Company.facts))
    )


def get_run(db: Session, run_id: int) -> ResearchRun | None:
    return db.get(ResearchRun, run_id)


def upsert_company(db: Session, data: dict[str, Any]) -> Company:
    number = data["company_number"]
    company = db.scalar(select(Company).where(Company.company_number == number))
    if company is None:
        company = Company(company_number=number)
        db.add(company)
    for field in (
        "legal_name",
        "organization_type",
        "status",
        "address",
        "postal_code",
        "city",
        "country",
        "website",
        "industry",
        "description",
    ):
        if data.get(field) is not None:
            setattr(company, field, data[field])
    company.last_researched_at = datetime.now(UTC)
    db.commit()
    db.refresh(company)
    return company


def add_fact(db: Session, company: Company, data: dict[str, Any]) -> CompanyFact:
    fact = CompanyFact(
        company_id=company.id,
        field_name=data["field"],
        value_json=data.get("value"),
        normalized_value=str(data.get("value")) if data.get("value") is not None else None,
        unit=data.get("unit"),
        status=data.get("status", "verified"),
        confidence=data.get("confidence"),
    )
    db.add(fact)
    db.commit()
    db.refresh(fact)
    return fact


def add_evidence(db: Session, fact: CompanyFact, data: dict[str, Any]) -> EvidenceRecord:
    url = data.get("source_url", "")
    evidence = EvidenceRecord(
        fact_id=fact.id,
        source_url=url,
        source_domain=urlparse(url).netloc or None,
        source_title=data.get("source_title"),
        source_type=data.get("source_type"),
        quoted_evidence=data.get("evidence", data.get("quoted_evidence", "")),
        published_at=data.get("published_at"),
        retrieved_at=datetime.now(UTC),
        content_hash=sha256(data.get("evidence", "").encode()).hexdigest()
        if data.get("evidence")
        else None,
        identity_match_score=data.get("identity_match_score"),
        evidence_score=data.get("confidence"),
    )
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


def persist_state(db: Session, company: Company, state: dict[str, Any]) -> None:
    for fact_data in state.get("verified_facts", []):
        fact = add_fact(db, company, fact_data)
        add_evidence(db, fact, fact_data)
    for event in state.get("events", []):
        if not event.get("source_url") or not event.get("title"):
            continue
        db.add(
            CompanyEvent(
                company_id=company.id,
                event_type=event.get("event_type", "other"),
                title=event["title"],
                description=event.get("description"),
                event_date=event.get("event_date"),
                source_url=event["source_url"],
                source_published_at=event.get("published_at"),
                retrieved_at=datetime.now(UTC),
            )
        )
    db.commit()


def finish_run(db: Session, run: ResearchRun, state: dict[str, Any], status: str) -> ResearchRun:
    run.finished_at = datetime.now(UTC)
    run.status = status
    run.request_count = state.get("request_count", 0)
    run.search_count = state.get("search_count", 0)
    run.estimated_cost = state.get("estimated_cost", 0.0)
    run.error_message = "\n".join(state.get("errors", [])) or None
    db.commit()
    db.refresh(run)
    return run
