from typing import Any

import httpx
from bs4 import BeautifulSoup

from .base import response_text, validate_public_url


class WebsiteSource:
    name = "website"

    async def search(self, company_number: str, query: str = "") -> list[dict[str, Any]]:
        """Search for company website using domain queries."""
        search_queries = [query] if query else [company_number]
        results = []

        async with httpx.AsyncClient(timeout=10) as client:
            for q in search_queries:
                try:
                    url = f"https://html.duckduckgo.com/?q={q}+site:.no"
                    response = await client.get(
                        url,
                        headers={
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                        },
                    )
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, "html.parser")
                        links = soup.find_all("a", {"class": "result__url"})
                        for link in links[:3]:
                            href = link.get("href")
                            if href and ".no" in href:
                                results.append(
                                    {"url": href, "title": link.get_text(), "source": "web_search"}
                                )
                except Exception:  # noqa: BLE001, S110 - search fallback is best effort
                    pass

        return results[:5]

    async def fetch(self, url: str) -> str:
        """Fetch website content after rejecting unsafe network targets."""
        validate_public_url(url)
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
                return response_text(response)
            except Exception as e:  # noqa: BLE001 - normalize transport errors
                raise ValueError(f"Failed to fetch {url}: {e}")

    async def extract(self, content: str) -> dict[str, Any]:
        """Extract structured data from website content."""
        soup = BeautifulSoup(content, "html.parser")

        for script in soup(["script", "style"]):
            script.decompose()

        text = soup.get_text(separator=" ", strip=True)

        return {
            "title": soup.title.string if soup.title else None,
            "text": text[:10000],
            "h1": [h.get_text() for h in soup.find_all("h1")][:3],
            "meta_description": soup.find("meta", attrs={"name": "description"}),
        }
