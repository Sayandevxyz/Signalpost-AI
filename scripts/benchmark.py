"""Compute honest metrics from a batch JSONL output."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def benchmark(path: str) -> dict:
    profiles = [
        json.loads(line)
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    requested = len(profiles)
    complete = sum(profile.get("research", {}).get("status") == "complete" for profile in profiles)
    partial = sum(profile.get("research", {}).get("status") == "partial" for profile in profiles)
    failed = sum(profile.get("research", {}).get("status") == "failed" for profile in profiles)
    success_with_facts = sum(complete and bool(profile.get("facts")) for profile in profiles)
    success_zero_facts = sum(complete and not profile.get("facts") for profile in profiles)
    facts = [fact for profile in profiles for fact in profile.get("facts", [])]
    evidenced = sum(
        bool(fact.get("evidence") or fact.get("quoted_evidence") or fact.get("source_url"))
        for fact in facts
    )
    records_with_verified_facts = sum(bool(profile.get("facts")) for profile in profiles)
    result = {
        "requested": requested,
        "processed": requested,
        "complete": complete,
        "partial": partial,
        "failed": failed,
        "success_with_facts": success_with_facts,
        "success_zero_facts": success_zero_facts,
        "facts": len(facts),
        "verified_facts": len(facts),
        "evidence_backed_facts": evidenced,
        "fact_bearing_companies": records_with_verified_facts,
        "records_with_verified_facts": records_with_verified_facts,
        "zero_fact_records": requested - records_with_verified_facts,
        "evidence_coverage": evidenced / len(facts) if facts else 0.0,
    }
    Path("data/output").mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(result, indent=2) + "\n"
    Path("data/output/benchmark.json").write_text(serialized, encoding="utf-8")
    Path("data/output/benchmark_summary.json").write_text(serialized, encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        default="data/output/profiles.jsonl",
        help="Generated research JSONL to measure; never use the canonical input dataset directly.",
    )
    args = parser.parse_args()
    print(json.dumps(benchmark(args.input), indent=2))
