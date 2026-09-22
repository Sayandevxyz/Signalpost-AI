from datetime import datetime
from typing import Any

from ..sources.website import WebsiteSource
from ..verification.identity import IdentityResolver


class WebsiteAgent:
    """Research company information from website and web sources."""

    def __init__(self):
        self.source = WebsiteSource()
        self.identity = IdentityResolver()

    async def research(
        self,
        company_number: str,
        company_identity: dict[str, Any]
    ) -> dict[str, Any]:
        """Search and extract website information."""
        results = {
            "candidate_facts": [],
            "source_documents": [],
            "errors": []
        }
        
        company_name = company_identity.get("legal_name", "")
        
        try:
            # Search for company website
            search_results = await self.source.search(company_number, company_name)
            
            for search_result in search_results:
                try:
                    content = await self.source.fetch(search_result["url"])
                    extracted = await self.source.extract(content)
                    
                    results["source_documents"].append({
                        "url": search_result["url"],
                        "title": search_result.get("title"),
                        "content": extracted,
                        "retrieved_at": datetime.utcnow().isoformat()
                    })
                    
                    # Add candidate facts (without hallucination)
                    if extracted.get("h1"):
                        results["candidate_facts"].append({
                            "field": "description",
                            "value": " ".join(extracted["h1"][:2]),
                            "source_url": search_result["url"],
                            "evidence": "Found in website heading",
                            "confidence": 0.5
                        })
                        
                except Exception as e:
                    results["errors"].append(f"Failed to fetch {search_result['url']}: {str(e)}")
                    
        except Exception as e:
            results["errors"].append(f"Website research failed: {str(e)}")
        
        return results
