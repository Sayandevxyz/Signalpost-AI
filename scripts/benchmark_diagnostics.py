"""Explain benchmark outcomes using only fields emitted by the research runner."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def diagnose(path: str) -> dict:
    records = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))

    details = []
    reasons = Counter()
    for profile in records:
        research = profile.get("research", {})
        facts = profile.get("facts", [])
        errors = [str(error) for error in research.get("errors", [])]
        identity = profile.get("company", {})
        resolved = bool(identity.get("legal_name") and identity.get("company_number"))
        source_url = identity.get("source_url")
        if facts:
            reason = None
            status = "success_with_facts"
        elif research.get("status") == "failed":
            reason = "research_failed"
            status = "failed"
        elif errors:
            reason = "research_errors"
            status = "partial"
        elif not resolved:
            reason = "identity_unresolved"
            status = "success_zero_facts"
        elif not source_url:
            reason = "no_identity_source"
            status = "success_zero_facts"
        else:
            reason = "no_verified_facts_after_source_research"
            status = "success_zero_facts"
        if reason:
            reasons[reason] += 1
        details.append(
            {
                "company_number": identity.get("company_number"),
                "status": status,
                "identity_resolved": resolved,
                "website_found": bool(research.get("website_found")),
                "sources_found": research.get("sources_found", 1 if source_url else 0),
                "candidate_facts": research.get("candidate_facts", len(facts)),
                "verified_facts": len(facts),
                "rejected_facts": research.get("rejected_facts", 0),
                "evidence_count": sum(
                    bool(fact.get("evidence") or fact.get("source_url")) for fact in facts
                ),
                "errors": errors,
                "reason": reason,
            }
        )

    report = {
        "total_companies": len(records),
        "status_counts": dict(Counter(detail["status"] for detail in details)),
        "reason_counts": dict(reasons),
        "records": details,
    }
    output = Path("data/output")
    output.mkdir(parents=True, exist_ok=True)
    (output / "benchmark_diagnostics.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    lines = [
        f"Total companies: {report['total_companies']}",
        f"Status counts: {json.dumps(report['status_counts'], sort_keys=True)}",
        f"Reason counts: {json.dumps(report['reason_counts'], sort_keys=True)}",
        "",
    ]
    for detail in details:
        if detail["status"] != "success_with_facts":
            lines.append(f"{detail['company_number']}: {detail['reason']}")
    (output / "benchmark_diagnostics.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/output/profiles-1000.jsonl")
    args = parser.parse_args()
    print(json.dumps(diagnose(args.input), indent=2))
