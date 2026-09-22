import ipaddress
import socket
from abc import ABC, abstractmethod
from typing import Any
from urllib.parse import urlparse

import httpx

from ..config import settings


def validate_public_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("only http and https URLs with a hostname are allowed")
    hostname = parsed.hostname.rstrip(".").lower()
    if hostname in {"localhost", "localhost.localdomain"}:
        raise ValueError("local hostnames are not allowed")
    try:
        addresses = {ipaddress.ip_address(hostname)}
    except ValueError:
        try:
            addresses = {
                ipaddress.ip_address(info[4][0])
                for info in socket.getaddrinfo(
                    hostname, parsed.port or 443, type=socket.SOCK_STREAM
                )
            }
        except socket.gaierror as exc:
            raise ValueError("hostname could not be resolved") from exc
    if any(
        address.is_private or address.is_loopback or address.is_link_local or address.is_reserved
        for address in addresses
    ):
        raise ValueError("private or local network targets are not allowed")
    return url


def response_text(response: httpx.Response) -> str:
    maximum = settings.max_response_size_mb * 1024 * 1024
    if len(response.content) > maximum:
        raise ValueError("response exceeds maximum configured size")
    return response.text


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
        return [
            {
                "url": f"https://data.brreg.no/enhetsregisteret/api/enheter/{query}",
                "company_number": query,
            }
        ]

    async def fetch(self, url: str) -> str:
        validate_public_url(url)
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            response = await client.get(url, headers={"Accept": "application/json"})
            response.raise_for_status()
            return response_text(response)

    async def extract(self, content: str) -> dict[str, Any]:
        import json

        return json.loads(content)
