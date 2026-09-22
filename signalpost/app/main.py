from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .agents.coordinator import ResearchCoordinator
from .extraction.normalizer import normalize_registration_number
from .sources.base import StaticRegistrySource

app = FastAPI(title="Signalpost AI", version="0.1.0")
coordinator = ResearchCoordinator([StaticRegistrySource()])
_runs: dict[str, dict] = {}

class ResearchRequest(BaseModel):
    company_number: str

@app.get("/")
async def root():
    return {"name": "Signalpost AI", "tagline": "Evidence-first company intelligence for Norwegian businesses."}

@app.get("/health")
async def health(): return {"status": "ok"}

@app.post("/research")
async def research(request: ResearchRequest):
    try: number = normalize_registration_number(request.company_number)
    except ValueError as exc: raise HTTPException(422, str(exc)) from exc
    state = await coordinator.research(number)
    run_id = f"{number}-{len(_runs)+1}"
    _runs[run_id] = state
    return {"company": state.get("company_identity", {}), "facts": state.get("verified_facts", []), "events": state.get("events", []), "verification": {"identity": True}, "research": {"run_id": run_id, "status": "partial" if state["errors"] else "complete", "errors": state["errors"]}}

@app.get("/research/{run_id}")
async def get_research(run_id: str):
    if run_id not in _runs: raise HTTPException(404, "Research run not found")
    return _runs[run_id]

@app.get("/companies/{company_number}")
async def get_company(company_number: str):
    try: number = normalize_registration_number(company_number)
    except ValueError as exc: raise HTTPException(422, str(exc)) from exc
    return await research(ResearchRequest(company_number=number))
