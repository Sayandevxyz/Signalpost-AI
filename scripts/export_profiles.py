"""Export JSONL profiles to JSONL and CSV-friendly records."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def export(input_path: str, output_dir: str) -> None:
    source = Path(input_path)
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    profiles = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines() if line.strip()]
    (destination / "company_profiles.jsonl").write_text("\n".join(json.dumps(item, default=str, ensure_ascii=False) for item in profiles) + "\n", encoding="utf-8")
    with (destination / "company_profiles.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["company_number", "legal_name", "status", "website", "fact_count", "event_count"])
        writer.writeheader()
        for profile in profiles:
            company = profile.get("company", {})
            writer.writerow({"company_number": company.get("company_number"), "legal_name": company.get("legal_name"), "status": company.get("status"), "website": company.get("website"), "fact_count": len(profile.get("facts", [])), "event_count": len(profile.get("events", []))})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/output/profiles.jsonl")
    parser.add_argument("--output-dir", default="data/output")
    args = parser.parse_args()
    export(args.input, args.output_dir)
