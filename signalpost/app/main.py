from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .agents.coordinator import ResearchCoordinator
from .database.database import get_db, init_db
from .database.models import Company, ResearchRun
from .database.repositories import get_company, get_run
from .extraction.normalizer import normalize_registration_number
from .sources.base import StaticRegistrySource

app = FastAPI(
    title="Signalpost AI",
    version="0.3.0",
    description="Evidence-first company intelligence for Norwegian businesses.",
)
coordinator = ResearchCoordinator([StaticRegistrySource()])


class ResearchRequest(BaseModel):
    company_number: str = Field(min_length=9, max_length=11)


@app.on_event("startup")
def startup() -> None:
    init_db()


def response_for(state: dict, run_id: int | str | None = None) -> dict:
    errors = state.get("errors", [])
    return {
        "company": state.get("company_identity", {}),
        "facts": state.get("verified_facts", []),
        "events": state.get("events", []),
        "verification": {
            "identity": not any("identity" in error.lower() for error in errors),
            "evidence": all(bool(fact.get("evidence")) for fact in state.get("verified_facts", [])),
        },
        "research": {
            "run_id": run_id or state.get("run_id"),
            "status": "failed"
            if errors and not state.get("company_identity")
            else ("partial" if errors else "complete"),
            "errors": errors,
            "request_count": state.get("request_count", 0),
            "search_count": state.get("search_count", 0),
            "estimated_cost": state.get("estimated_cost", 0.0),
            "started_at": state.get("started_at"),
            "finished_at": state.get("finished_at"),
        },
    }


def response_from_database(run: ResearchRun, db: Session) -> dict:
    company = db.get(Company, run.company_id) if run.company_id else None
    if company is None:
        raise HTTPException(status_code=404, detail="Research company not found")
    facts = [
        {
            "field": fact.field_name,
            "value": fact.value_json,
            "unit": fact.unit,
            "status": fact.status,
            "confidence": fact.confidence,
            "is_current": fact.is_current,
            "evidence": fact.evidence[0].quoted_evidence if fact.evidence else "",
            "source_url": fact.evidence[0].source_url if fact.evidence else "",
        }
        for fact in company.facts
        if fact.is_current
    ]
    events = [
        {
            "event_type": event.event_type,
            "title": event.title,
            "description": event.description,
            "source_url": event.source_url,
        }
        for event in company.events
    ]
    return {
        "company": {
            "company_number": company.company_number,
            "legal_name": company.legal_name,
            "status": company.status,
            "website": company.website,
            "address": company.address,
            "city": company.city,
            "country": company.country,
        },
        "facts": facts,
        "events": events,
        "verification": {
            "identity": True,
            "evidence": all(bool(fact["evidence"]) for fact in facts),
        },
        "research": {
            "run_id": run.id,
            "status": run.status,
            "errors": run.error_message.splitlines() if run.error_message else [],
            "request_count": run.request_count,
            "search_count": run.search_count,
            "estimated_cost": run.estimated_cost,
            "started_at": run.started_at,
            "finished_at": run.finished_at,
        },
    }


@app.get("/")
async def root() -> dict:
    return {
        "name": "Signalpost AI",
        "tagline": "Evidence-first company intelligence for Norwegian businesses.",
        "docs": "/docs",
    }


@app.get("/health")
async def health(db: Session = Depends(get_db)) -> dict:  # noqa: B008
    db.execute(__import__("sqlalchemy").text("SELECT 1"))
    return {"status": "ok"}


@app.post("/research")
async def research(request: ResearchRequest) -> dict:
    try:
        number = normalize_registration_number(request.company_number)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    state = await coordinator.research(number)
    return response_for(state, state.get("run_id"))


@app.get("/research/{run_id}")
async def get_research(run_id: str, db: Session = Depends(get_db)) -> dict:  # noqa: B008
    try:
        numeric_run_id = int(run_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Research run not found") from None
    run = get_run(db, numeric_run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Research run not found")
    return response_from_database(run, db)


@app.get("/companies/{company_number}")
async def get_company_profile(company_number: str, db: Session = Depends(get_db)) -> dict:  # noqa: B008
    try:
        number = normalize_registration_number(company_number)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    company = get_company(db, number)
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return (
        response_from_database(company.research_runs[-1], db)
        if getattr(company, "research_runs", None)
        else {
            "company": {"company_number": company.company_number, "legal_name": company.legal_name},
            "facts": [],
            "events": [],
        }
    )
