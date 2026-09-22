from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ExtractedFact(BaseModel):
    field: str
    value: Any = None
    unit: str | None = None
    source_url: str
    quoted_evidence: str
    published_at: datetime | None = None
    confidence: float = 0.8


class FactExtractor:
    """Extract structured facts from raw content."""

    def extract_from_registry(self, data: dict[str, Any], source_url: str) -> list[ExtractedFact]:
        """Extract facts from official registry JSON."""
        facts = []

        field_map = {
            "legal_name": ("navn", "Legal name from registry"),
            "status": ("status", "Organization status"),
            "address": ("forretningsadresse.adresse", "Official business address"),
            "postal_code": ("forretningsadresse.postnummer", "Postal code"),
            "city": ("forretningsadresse.poststed", "City"),
            "organization_type": ("organisasjonsform", "Organization type"),
            "employees": ("antallAnsatte", "Number of employees"),
        }

        for field, (json_key, description) in field_map.items():
            value = self._get_nested(data, json_key)
            if value is not None:
                facts.append(
                    ExtractedFact(
                        field=field,
                        value=value,
                        source_url=source_url,
                        quoted_evidence=description,
                        confidence=0.95,
                    )
                )

        return facts

    def extract_from_website(self, data: dict[str, Any], source_url: str) -> list[ExtractedFact]:
        """Extract facts from website content."""
        facts = []

        return facts

    def extract_from_news(self, data: dict[str, Any], source_url: str) -> list[ExtractedFact]:
        """Extract events/facts from news content."""
        events = []

        return events

    @staticmethod
    def _get_nested(data: dict, key: str) -> Any:
        """Get nested dict value using dot notation."""
        keys = key.split(".")
        value = data
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return None
        return value
