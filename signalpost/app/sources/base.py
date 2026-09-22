from abc import ABC, abstractmethod
from typing import Any

import httpx


class SourceAdapter(ABC):
    name = "source"
    @abstractmethod
    async def search(self, query: str) -> list[dict[str, Any]]: ...
    @abstractmethod
    async def fetch(self, url: str) -> str: ...
    async def extract(self, content: str) -> dict[str, Any]:
        return {"content": content}

class StaticRegistrySource(SourceAdapter):
    name = "official_registry"
    async def search(self, query: str) -> list[dict[str, Any]]:
        return [{"url": f"https://data.brreg.no/enhetsregisteret/api/enheter/{query}", "company_number": query}]
    async def fetch(self, url: str) -> str:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            response = await client.get(url, headers={"Accept": "application/json"})
            response.raise_for_status()
            if len(response.content) > 2_000_000:
                raise ValueError("registry response exceeds maximum size")
            return response.text

    async def extract(self, content: str) -> dict[str, Any]:
        import json
        return json.loads(content)
