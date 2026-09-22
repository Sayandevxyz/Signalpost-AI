from __future__ import annotations

import re
from typing import Any


def normalize_name(name: str | None) -> str:
    return re.sub(r"[^a-z0-9]", "", (name or "").lower().replace("as", ""))


class IdentityResolver:
    def score(self, target: dict[str, Any], source: dict[str, Any]) -> float:
        if (
            target.get("company_number")
            and source.get("company_number") == target["company_number"]
        ):
            return 1.0
        score = 0.0
        if normalize_name(target.get("legal_name")) == normalize_name(source.get("legal_name")):
            score += 0.55
        if target.get("address") and target.get("address") == source.get("address"):
            score += 0.2
        if target.get("website") and target.get("website") == source.get("website"):
            score += 0.2
        if target.get("organization_type") and target.get("organization_type") == source.get(
            "organization_type"
        ):
            score += 0.05
        return min(score, 1.0)

    def matches(
        self, target: dict[str, Any], source: dict[str, Any], threshold: float = 0.8
    ) -> bool:
        return self.score(target, source) >= threshold
