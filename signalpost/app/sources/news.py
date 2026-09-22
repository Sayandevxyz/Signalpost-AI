from typing import Any

import httpx


class NewsSource:
    name = "news"

    async def search(self, company_number: str, company_name: str = "") -> list[dict[str, Any]]:
        """Search for news about company."""
        queries = [company_name] if company_name else [company_number]
        results = []
        
        async with httpx.AsyncClient(timeout=10) as client:
            for q in queries:
                try:
                    # Mock news search - in production use real news API
                    # For demo, we return empty to avoid API calls
                    pass
                except Exception:
                    pass
        
        return results

    async def fetch(self, url: str) -> str:
        """Fetch news article."""
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
                if len(response.content) > 5_000_000:
                    raise ValueError("news response exceeds maximum size")
                return response.text
            except Exception as e:
                raise ValueError(f"Failed to fetch news: {e}")

    async def extract(self, content: str) -> list[dict[str, Any]]:
        """Extract news events from content."""
        return []
