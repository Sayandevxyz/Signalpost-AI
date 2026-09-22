import asyncio
from datetime import datetime
from typing import Any

from ..agents.coordinator import ResearchCoordinator
from ..agents.registry_agent import RegistryAgent
from ..agents.website_agent import WebsiteAgent
from ..agents.financial_agent import FinancialAgent
from ..agents.news_agent import NewsAgent
from ..agents.verification_agent import VerificationAgent
from ..verification.freshness import FreshnessChecker
from ..sources.base import StaticRegistrySource
from .state import ResearchState


class ResearchGraph:
    """LangGraph-style research workflow for company intelligence."""

    def __init__(self):
        self.coordinator = ResearchCoordinator([StaticRegistrySource()])
        self.registry = RegistryAgent()
        self.website = WebsiteAgent()
        self.financial = FinancialAgent()
        self.news = NewsAgent()
        self.verifier = VerificationAgent()
        self.freshness = FreshnessChecker()

    async def execute(self, company_number: str) -> ResearchState:
        """Execute full research workflow."""
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
            "started_at": datetime.utcnow(),
        }

        try:
            # Step 1: Resolve company identity from registry
            state = await self._resolve_company(state)
            
            if not state.get("company_identity"):
                state["errors"].append("Failed to resolve company identity")
                state["finished_at"] = datetime.utcnow()
                return state
            
            # Step 2: Parallel research from multiple sources
            state = await self._parallel_research(state)
            
            # Step 3: Normalize and verify facts
            state = await self._verify_facts(state)
            
            # Step 4: Apply freshness logic
            state = await self._apply_freshness(state)
            
            state["finished_at"] = datetime.utcnow()
            
        except Exception as e:
            state["errors"].append(f"Research workflow error: {str(e)}")
            state["finished_at"] = datetime.utcnow()
        
        return state

    async def _resolve_company(self, state: ResearchState) -> ResearchState:
        """Step 1: Resolve exact company from registry."""
        try:
            registry_result = await self.registry.research(state["company_number"])
            state["company_identity"] = registry_result.get("company_identity", {})
            state["candidate_facts"].extend(registry_result.get("facts", []))
            state["source_documents"].extend(registry_result.get("source_documents", []))
            state["request_count"] += registry_result.get("request_count", 0)
            state["search_count"] += registry_result.get("search_count", 0)
            state["errors"].extend(registry_result.get("errors", []))
        except Exception as e:
            state["errors"].append(f"Registry resolution failed: {str(e)}")
        
        return state

    async def _parallel_research(self, state: ResearchState) -> ResearchState:
        """Step 2: Run website, financial, and news research in parallel."""
        try:
            results = await asyncio.gather(
                self.website.research(state["company_number"], state.get("company_identity", {})),
                self.financial.research(state["company_number"], state.get("company_identity", {})),
                self.news.research(state["company_number"], state.get("company_identity", {})),
                return_exceptions=True
            )
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    state["errors"].append(f"Parallel research error: {str(result)}")
                else:
                    state["candidate_facts"].extend(result.get("candidate_facts", []))
                    state["source_documents"].extend(result.get("source_documents", []))
                    state["events"].extend(result.get("events", []))
                    state["errors"].extend(result.get("errors", []))
            
        except Exception as e:
            state["errors"].append(f"Parallel research failed: {str(e)}")
        
        return state

    async def _verify_facts(self, state: ResearchState) -> ResearchState:
        """Step 3: Verify facts match identity and evidence."""
        try:
            verified, rejected = self.verifier.verify_facts(
                state["candidate_facts"],
                state.get("company_identity", {})
            )
            state["verified_facts"] = verified
            state["rejected_facts"] = rejected
        except Exception as e:
            state["errors"].append(f"Fact verification failed: {str(e)}")
        
        return state

    async def _apply_freshness(self, state: ResearchState) -> ResearchState:
        """Step 4: Apply freshness logic and conflict resolution."""
        try:
            # Group facts by field
            facts_by_field = {}
            for fact in state["verified_facts"]:
                field = fact.get("field")
                if field:
                    if field not in facts_by_field:
                        facts_by_field[field] = []
                    facts_by_field[field].append(fact)
            
            # For each field, keep only the freshest fact
            final_facts = []
            for field, facts in facts_by_field.items():
                if facts:
                    # Sort by some freshness criteria and pick the best
                    best = max(facts, key=lambda f: f.get("confidence", 0))
                    best["is_current"] = True
                    final_facts.append(best)
            
            state["verified_facts"] = final_facts
            
        except Exception as e:
            state["errors"].append(f"Freshness check failed: {str(e)}")
        
        return state
