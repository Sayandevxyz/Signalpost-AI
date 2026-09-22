import json
import sys
from pathlib import Path
from urllib.parse import urlparse

path = Path(sys.argv[1] if len(sys.argv) > 1 else "data/output/company_profiles.jsonl")
total = valid = evidence_facts = total_facts = identity_verified = financial_facts = (
    financial_evidence
) = 0
seen_numbers: set[str] = set()
if path.exists():
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        total += 1
        try:
            profile = json.loads(line)
            number = str(profile.get("company", {}).get("company_number", ""))
            duplicate = not number or number in seen_numbers
            seen_numbers.add(number)
            facts = profile.get("facts", [])
            total_facts += len(facts)
            evidence_facts += sum(bool(f.get("evidence")) for f in facts)
            financial = [
                f
                for f in facts
                if f.get("field")
                in {"revenue", "profit", "assets", "liabilities", "equity", "employees"}
            ]
            financial_facts += len(financial)
            financial_evidence += sum(bool(f.get("evidence")) for f in financial)
            identity = profile.get("verification", {}).get("identity", True)
            identity_verified += bool(identity)
            urls_valid = all(
                urlparse(e.get("source_url", "")).scheme in {"http", "https"}
                for f in facts
                for e in f.get("evidence", [])
                if isinstance(e, dict)
            )
            if not duplicate and urls_valid and all(f.get("evidence") for f in facts):
                valid += 1
        except (json.JSONDecodeError, TypeError, AttributeError):
            continue

pct = lambda value, denominator: round(100 * value / denominator, 1) if denominator else 0.0
print(f"Dataset validation  Companies: {total} Valid: {valid} Invalid: {total - valid}")
print(
    f"Evidence coverage: {pct(evidence_facts, total_facts)}% Identity verification: {pct(identity_verified, total)}% Financial evidence coverage: {pct(financial_evidence, financial_facts)}%"
)
