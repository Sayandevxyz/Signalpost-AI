"""Compute honest metrics from a batch JSONL output."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def benchmark(path: str) -> dict:
    profiles = [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
    total = len(profiles)
    successful = sum(profile.get("research", {}).get("status") == "complete" for profile in profiles)
    facts = [fact for profile in profiles for fact in profile.get("facts", [])]
    evidenced = sum(bool(fact.get("evidence") or fact.get("source_url")) for fact in facts)
    result = {"companies_processed": total, "success_rate": successful / total if total else 0.0, "evidence_rate": evidenced / len(facts) if facts else 0.0, "facts": len(facts)}
    Path("data/output").mkdir(parents=True, exist_ok=True)
    Path("data/output/benchmark.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/output/profiles.jsonl")
    args = parser.parse_args()
    print(json.dumps(benchmark(args.input), indent=2))
