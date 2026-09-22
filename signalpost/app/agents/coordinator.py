from datetime import datetime
import json

from ..agents.registry_agent import RegistryAgent
from ..graph.state import ResearchState
from ..verification.evidence import EvidenceVerifier
from ..verification.freshness import FreshnessChecker
from ..verification.identity import IdentityResolver


class ResearchCoordinator:
    def __init__(self, sources=None):
        self.sources = sources or []
        self.identity = IdentityResolver()
        self.registry = RegistryAgent()
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
                    document = {**result, "content": content, "source": source.name}
                    state["source_documents"].append(document)
                    if source.name == "official_registry" and content:
                        payload = await source.extract(content)
                        identity = self.registry.extract(payload, result["url"])
                        identity["country"] = "Norway"
                        state["company_identity"] = identity
                        state["candidate_facts"].extend(
                            {"field": field, "value": identity.get(field), "source_url": result["url"], "evidence": json.dumps(payload)}
                            for field in ("legal_name", "status", "address", "organization_type")
                            if identity.get(field)
                        )
            except Exception as exc:
                state["errors"].append(f"{source.name}: {exc}")
        state.setdefault("company_identity", {"company_number": company_number, "country": "Norway"})
        state["verified_facts"] = [fact for fact in state["candidate_facts"] if self.evidence.verify(fact, fact["evidence"])]
        state["finished_at"] = datetime.utcnow()
        return state
