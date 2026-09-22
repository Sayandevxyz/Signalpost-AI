from abc import ABC, abstractmethod
from typing import Any


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
        return ""
