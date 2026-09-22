"""FastAPI application for Signalpost AI."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .agents.coordinator import ResearchCoordinator
from .extraction.normalizer import normalize_registration_number
from .sources.base import StaticRegistrySource

app = FastAPI(
    title="Signalpost AI",
    version="0.2.0",
    description="Evidence-first company intelligence for Norwegian businesses.",
)
coordinator = ResearchCoordinator([StaticRegistrySource()])
_runs: dict[str, dict] = {}


class ResearchRequest(BaseModel):
    company_number: str = Field(min_length=9, max_length=11)


def response_for(state: dict, run_id: str | None = None) -> dict:
    return {
        "company": state.get("company_identity", {}),
        "facts": state.get("verified_facts", []),
        "events": state.get("events", []),
        "verification": {"identity": not bool(state.get("errors"))},
        "research": {
            "run_id": run_id,
            "status": "partial" if state.get("errors") else "complete",
            "errors": state.get("errors", []),
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
async def health() -> dict:
    return {"status": "ok"}


@app.post("/research")
async def research(request: ResearchRequest) -> dict:
    try:
        number = normalize_registration_number(request.company_number)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    state = await coordinator.research(number)
    run_id = f"{number}-{len(_runs) + 1}"
    _runs[run_id] = state
    return response_for(state, run_id)


@app.get("/research/{run_id}")
async def get_research(run_id: str) -> dict:
    if run_id not in _runs:
        raise HTTPException(status_code=404, detail="Research run not found")
    return response_for(_runs[run_id], run_id)


@app.get("/companies/{company_number}")
async def get_company(company_number: str) -> dict:
    return await research(ResearchRequest(company_number=company_number))
