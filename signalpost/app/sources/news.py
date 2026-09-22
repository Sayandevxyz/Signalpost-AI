from typing import Any

import httpx


class NewsSource:
    name = "news"

    async def search(self, company_number: str, company_name: str = "") -> list[dict[str, Any]]:
        """Search for news about company."""
        return []

    async def fetch(self, url: str) -> str:
        """Fetch news article."""
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
                if len(response.content) > 5_000_000:
                    raise ValueError("news response exceeds maximum size")
                return response.text
            except Exception as e:  # noqa: BLE001 - normalize transport errors
                raise ValueError(f"Failed to fetch news: {e}")

    async def extract(self, content: str) -> list[dict[str, Any]]:
        """Extract news events from content."""
        return []
