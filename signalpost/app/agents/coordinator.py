from __future__ import annotations

import asyncio
import hashlib
from datetime import UTC, datetime
from typing import Any, Callable
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from ..agents.financial_agent import FinancialAgent
from ..agents.news_agent import NewsAgent
from ..agents.registry_agent import RegistryAgent
from ..agents.verification_agent import VerificationAgent
from ..agents.website_agent import WebsiteAgent
from ..database import repositories
from ..database.database import SessionLocal, init_db
from ..graph.state import ResearchState
from ..verification.freshness import FreshnessChecker
from ..sources.base import StaticRegistrySource


class ResearchCoordinator:
    """Coordinate registry-first research and persist verified results."""

    def __init__(
        self,
        sources: list[Any] | None = None,
        session_factory: Callable[[], Session] | None = SessionLocal,
    ) -> None:
        self.registry = RegistryAgent((sources or [StaticRegistrySource()])[0])
        self.website = WebsiteAgent()
        self.financial = FinancialAgent()
        self.news = NewsAgent()
        self.verifier = VerificationAgent()
        self.freshness = FreshnessChecker()
        self.session_factory = session_factory

    async def research(self, company_number: str) -> ResearchState:
        started = datetime.now(UTC)
        state: ResearchState = {
            "company_number": company_number,
            "company_identity": {},
            "source_documents": [],
            "candidate_facts": [],
            "verified_facts": [],
            "rejected_facts": [],
            "events": [],
            "errors": [],
            "request_count": 0,
            "search_count": 0,
            "estimated_cost": 0.0,
            "started_at": started,
        }
        company = None
        run = None
        db = None
        try:
            registry = await self.registry.research(company_number)
            self._merge(state, registry)
            identity = registry.get("company_identity", {})
            if not identity.get("company_number"):
                state["company_identity"] = {"company_number": company_number, "country": "Norway"}
                identity = state["company_identity"]
            if identity.get("company_number") != company_number:
                state["errors"].append("Registry identity did not match requested company number")
            else:
                downstream = await asyncio.gather(
                    self.website.research(company_number, identity),
                    self.financial.research(company_number, identity),
                    self.news.research(company_number, identity),
                    return_exceptions=True,
                )
                for result in downstream:
                    if isinstance(result, Exception):
                        state["errors"].append(f"downstream research failed: {result}")
                    else:
                        self._merge(state, result)

            verified, rejected = self.verifier.verify_facts(
                state["candidate_facts"], state.get("company_identity", {})
            )
            state["verified_facts"] = verified
            state["rejected_facts"] = rejected
            state["verified_facts"] = self._freshest(verified)

            if self.session_factory is not None:
                init_db()
                db = self.session_factory()
                company = repositories.upsert_company(db, state.get("company_identity", {}) or {"company_number": company_number})
                run = repositories.start_run(db, company)
                repositories.persist_state(db, company, state)
                repositories.finish_run(
                    db,
                    run,
                    state,
                    status="partial" if state["errors"] else "complete",
                )
                state["run_id"] = run.id
        except Exception as exc:  # noqa: BLE001 - preserve partial research
            state["errors"].append(str(exc))
            if db is not None and run is not None:
                repositories.finish_run(db, run, state, status="failed")
        finally:
            if db is not None:
                db.close()
            state["finished_at"] = datetime.now(UTC)
        return state

    @staticmethod
    def _merge(state: ResearchState, result: dict[str, Any]) -> None:
        state["candidate_facts"].extend(result.get("facts", result.get("candidate_facts", [])))
        state["source_documents"].extend(result.get("source_documents", []))
        state["events"].extend(result.get("events", []))
        state["errors"].extend(result.get("errors", []))
        state["request_count"] += result.get("request_count", 0)
        state["search_count"] += result.get("search_count", 0)

    @staticmethod
    def _freshest(facts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        selected: dict[str, dict[str, Any]] = {}
        for fact in facts:
            field = fact.get("field")
            if not field:
                continue
            evidence = fact.get("evidence", "")
            fact["is_current"] = True
            current = selected.get(field)
            if current is None or len(evidence) > len(current.get("evidence", "")):
                selected[field] = fact
        return list(selected.values())
