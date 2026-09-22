import pytest

from signalpost.app.extraction.normalizer import normalize_registration_number
from signalpost.app.verification.evidence import EvidenceVerifier
from signalpost.app.verification.freshness import FreshnessChecker
from signalpost.app.verification.identity import IdentityResolver


def test_registration_number():
    assert normalize_registration_number("912 345 678") == "912345678"
    with pytest.raises(ValueError):
        normalize_registration_number("123")


def test_identity_number_wins():
    r = IdentityResolver()
    assert r.matches(
        {"company_number": "1", "legal_name": "A AS"},
        {"company_number": "1", "legal_name": "Other"},
    )
    assert not r.matches(
        {"company_number": "1", "legal_name": "A AS"}, {"company_number": "2", "legal_name": "A AS"}
    )


def test_evidence_requires_quote():
    v = EvidenceVerifier()
    assert v.verify({"evidence": "Revenue was 10 NOK"}, "Revenue was 10 NOK for 2025")
    assert not v.verify({"evidence": "missing"}, "source")


def test_freshness_preserves_history():
    facts = [
        {"field": "employees", "value": 42, "published_at": "2025-01-01"},
        {"field": "employees", "value": 61, "published_at": "2026-01-01"},
    ]
    result = FreshnessChecker().choose_current(facts)
    assert next(f for f in result if f["is_current"])["value"] == 61
