from datetime import datetime

from ..graph.state import ResearchState
from ..verification.evidence import EvidenceVerifier
from ..verification.freshness import FreshnessChecker
from ..verification.identity import IdentityResolver


class ResearchCoordinator:
    def __init__(self, sources=None):
        self.sources = sources or []
        self.identity = IdentityResolver()
        self.evidence = EvidenceVerifier()
        self.freshness = FreshnessChecker()

    async def research(self, company_number: str) -> ResearchState:
        started = datetime.utcnow()
        state: ResearchState = {"company_number": company_number, "source_documents": [], "candidate_facts": [], "verified_facts": [], "rejected_facts": [], "events": [], "errors": [], "request_count": 0, "search_count": 0, "estimated_cost": 0.0, "started_at": started}
        for source in self.sources:
            try:
                results = await source.search(company_number)
                state["search_count"] += 1
                for result in results:
                    content = await source.fetch(result["url"])
                    state["request_count"] += 1
                    state["source_documents"].append({**result, "content": content, "source": source.name})
            except Exception as exc:
                state["errors"].append(f"{source.name}: {exc}")
        state["company_identity"] = {"company_number": company_number, "country": "Norway"}
        state["finished_at"] = datetime.utcnow()
        return state
