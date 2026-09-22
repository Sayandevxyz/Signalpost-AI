from typing import Any

from ..verification.evidence import EvidenceVerifier
from ..verification.identity import IdentityResolver


class VerificationAgent:
    """Verify facts match correct company and evidence supports claims."""

    def __init__(self):
        self.identity = IdentityResolver()
        self.evidence = EvidenceVerifier()

    def verify_facts(
        self, candidate_facts: list[dict[str, Any]], company_identity: dict[str, Any]
    ) -> tuple[list[dict], list[dict]]:
        """Separate verified facts from rejected facts."""
        verified = []
        rejected = []

        for fact in candidate_facts:
            # Check if evidence exists and is meaningful
            evidence = fact.get("evidence", "")
            if not evidence or not isinstance(evidence, str) or len(evidence.strip()) < 5:
                rejected.append({**fact, "rejection_reason": "Insufficient evidence"})
                continue

            # Check confidence threshold
            confidence = fact.get("confidence", 0)
            if confidence < 0.6:
                rejected.append({**fact, "rejection_reason": f"Low confidence: {confidence}"})
                continue

            # Verify evidence supports the claim
            if self.evidence.verify(fact, evidence):
                verified.append(fact)
            else:
                rejected.append({**fact, "rejection_reason": "Evidence does not support claim"})

        return verified, rejected

    def verify_identity(
        self, source_data: dict[str, Any], target_identity: dict[str, Any]
    ) -> float:
        """Score how well source data matches target identity."""
        return self.identity.score(target_identity, source_data)
