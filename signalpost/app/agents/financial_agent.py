from datetime import UTC, datetime
from typing import Any

from ..extraction.fact_extractor import FactExtractor
from ..sources.financial import FinancialSource


class FinancialAgent:
    """Research financial information about company."""

    def __init__(self):
        self.source = FinancialSource()
        self.extractor = FactExtractor()

    async def research(
        self, company_number: str, company_identity: dict[str, Any]
    ) -> dict[str, Any]:
        """Search and extract financial information."""
        results = {"candidate_facts": [], "source_documents": [], "errors": []}

        try:
            search_results = await self.source.search(company_number)

            for search_result in search_results:
                try:
                    content = await self.source.fetch(search_result["url"])
                    extracted = await self.source.extract(content)

                    results["source_documents"].append(
                        {
                            "url": search_result["url"],
                            "source": search_result.get("source"),
                            "content": extracted,
                            "retrieved_at": datetime.now(UTC).isoformat(),
                        }
                    )

                    # Extract facts using deterministic extraction
                    import json

                    data = json.loads(content) if isinstance(content, str) else content
                    facts = self.extractor.extract_from_registry(data, search_result["url"])

                    for fact in facts:
                        # Only include financial facts if they meet confidence threshold
                        if (
                            fact.field in ("employees", "revenue", "profit", "assets")
                            and fact.confidence >= 0.8
                        ):
                            results["candidate_facts"].append(
                                {
                                    "field": fact.field,
                                    "value": fact.value,
                                    "unit": fact.unit,
                                    "source_url": fact.source_url,
                                    "evidence": fact.quoted_evidence,
                                    "confidence": fact.confidence,
                                }
                            )

                except Exception as e:  # noqa: BLE001 - preserve partial research
                    results["errors"].append(f"Failed to extract financial data: {e!s}")

        except Exception as e:  # noqa: BLE001 - preserve partial research
            results["errors"].append(f"Financial research failed: {e!s}")

        return results
