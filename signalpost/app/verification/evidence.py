from typing import Any


class EvidenceVerifier:
    def verify(self, fact: dict[str, Any], document: str) -> bool:
        quote = fact.get("evidence") or fact.get("quoted_evidence")
        if not quote or not document:
            return False
        return quote.strip() in document

    def validate(self, fact: dict[str, Any], identity_score: float) -> bool:
        return identity_score >= 0.8 and bool(fact.get("source_url")) and bool(fact.get("evidence") or fact.get("quoted_evidence"))
