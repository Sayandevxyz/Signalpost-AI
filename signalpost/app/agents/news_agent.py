from datetime import UTC, datetime
from typing import Any

from ..sources.news import NewsSource


class NewsAgent:
    """Research recent news and events about company."""

    def __init__(self):
        self.source = NewsSource()

    async def research(
        self, company_number: str, company_identity: dict[str, Any]
    ) -> dict[str, Any]:
        """Search and extract news events."""
        results = {"events": [], "source_documents": [], "errors": []}

        company_name = company_identity.get("legal_name", "")

        try:
            search_results = await self.source.search(company_number, company_name)

            for search_result in search_results:
                try:
                    content = await self.source.fetch(search_result["url"])
                    extracted = await self.source.extract(content)

                    results["source_documents"].append(
                        {
                            "url": search_result["url"],
                            "content": extracted,
                            "retrieved_at": datetime.now(UTC).isoformat(),
                        }
                    )

                                results["events"].extend(extracted)

                except Exception as e:  # noqa: BLE001 - preserve partial research
                    results["errors"].append(f"Failed to extract news: {e!s}")

        except Exception as e:  # noqa: BLE001 - preserve partial research
            results["errors"].append(f"News research failed: {e!s}")

        return results
