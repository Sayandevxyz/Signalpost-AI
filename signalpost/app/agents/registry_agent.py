from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from ..extraction.fact_extractor import FactExtractor
from ..sources.base import StaticRegistrySource


class RegistryAgent:
    def __init__(self, source: StaticRegistrySource | None = None):
        self.source = source or StaticRegistrySource()
        self.extractor = FactExtractor()

    def extract(self, payload: dict[str, Any], source_url: str) -> dict[str, Any]:
        address = payload.get("forretningsadresse") or payload.get("address") or {}
        if isinstance(address, dict):
            address_text = ", ".join(address.get("adresse", [])) or address.get("address")
        else:
            address_text = str(address) if address else None
        return {
            "company_number": str(
                payload.get("organizationNumber")
                or payload.get("organisasjonsnummer")
                or payload.get("company_number")
                or ""
            ),
            "legal_name": payload.get("name") or payload.get("navn") or payload.get("legal_name"),
            "status": payload.get("status")
            or ("active" if payload.get("registrertIEnhetsregisteret") else None),
            "address": address_text,
            "postal_code": address.get("postnummer") if isinstance(address, dict) else None,
            "city": address.get("poststed") if isinstance(address, dict) else None,
            "organization_type": (
                payload.get("organizationForm")
                or payload.get("organisasjonsform", {}).get("beskrivelse")
                if isinstance(payload.get("organisasjonsform"), dict)
                else payload.get("organisasjonsform")
            )
            or payload.get("organization_type"),
            "source_url": source_url,
        }

    async def research(self, company_number: str) -> dict[str, Any]:
        result: dict[str, Any] = {
            "company_identity": {},
            "facts": [],
            "source_documents": [],
            "errors": [],
            "request_count": 0,
            "search_count": 0,
        }
        try:
            results = await self.source.search(company_number)
            result["search_count"] = 1
            for item in results:
                content = await self.source.fetch(item["url"])
                result["request_count"] += 1
                payload = await self.source.extract(content)
                identity = self.extract(payload, item["url"])
                if identity.get("company_number") != company_number:
                    result["errors"].append(
                        "Registry response company number did not match requested number"
                    )
                    continue
                result["company_identity"] = identity
                result["source_documents"].append(
                    {
                        "url": item["url"],
                        "content": payload,
                        "retrieved_at": datetime.now(UTC).isoformat(),
                        "source": self.source.name,
                    }
                )
                result["facts"] = [
                    fact.model_dump(mode="json")
                    for fact in self.extractor.extract_from_registry(payload, item["url"])
                ]
        except Exception as exc:  # noqa: BLE001 - preserve partial research
            result["errors"].append(str(exc))
        return result
