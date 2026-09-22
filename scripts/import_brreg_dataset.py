from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path

SOURCE_NAME = "Brønnøysundregistrene Enhetsregisteret"
SOURCE_URL = "https://data.brreg.no/enhetsregisteret/api/enheter/lastned/csv"
INDIVIDUAL_URL = "https://data.brreg.no/enhetsregisteret/api/enheter/{organisasjonsnummer}"
LICENSE = "NLOD 2.0"
LICENSE_URL = "https://data.norge.no/nlod/en/2.0"
NUMBER_PATTERN = re.compile(r"^\d{9}$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import real organization numbers from an official Brønnøysundregistrene CSV export.")
    parser.add_argument("--input", type=Path, default=Path("data/raw/enhetsregisteret.csv"))
    parser.add_argument("--output", type=Path, default=Path("data/input/norwegian_companies.jsonl"))
    parser.add_argument("--manifest", type=Path, default=Path("data/input/dataset_manifest.json"))
    parser.add_argument("--min-records", type=int, default=1000)
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def import_dataset(input_path: Path, output_path: Path, manifest_path: Path, minimum: int) -> dict[str, object]:
    seen: set[str] = set()
    source_records = valid = invalid = duplicates = 0
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with input_path.open("r", encoding="utf-8-sig", newline="") as source, output_path.open("w", encoding="utf-8") as output:
        sample = source.read(8192)
        source.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        except csv.Error:
            dialect = csv.excel
        reader = csv.DictReader(source, dialect=dialect)
        if not reader.fieldnames or "organisasjonsnummer" not in reader.fieldnames:
            raise ValueError(f"Missing organisasjonsnummer column; found {reader.fieldnames!r}")
        for row in reader:
            source_records += 1
            number = str(row.get("organisasjonsnummer") or "").strip()
            if not NUMBER_PATTERN.fullmatch(number):
                invalid += 1
                continue
            if number in seen:
                duplicates += 1
                continue
            seen.add(number)
            output.write(json.dumps({"company_number": number}, ensure_ascii=False) + "\n")
            valid += 1

    if valid < minimum:
        raise RuntimeError(f"Only {valid} valid unique organization numbers found; minimum is {minimum}")

    retrieved_at = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    manifest = {
        "source_name": SOURCE_NAME,
        "source_url": SOURCE_URL,
        "endpoint": INDIVIDUAL_URL,
        "license": LICENSE,
        "license_url": LICENSE_URL,
        "retrieved_at": retrieved_at,
        "source_sha256": sha256(input_path),
        "source_records": source_records,
        "record_count": valid,
        "valid_unique_company_numbers": valid,
        "invalid_records": invalid,
        "duplicate_records": duplicates,
        "entity_scope": "Enhetsregisteret entities; organization numbers are not asserted to be commercial companies.",
        "transformation_script": "scripts/import_brreg_dataset.py",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    args = parse_args()
    manifest = import_dataset(args.input, args.output, args.manifest, args.min_records)
    print(f"source file: {args.input}")
    print(f"source record count: {manifest['source_records']}")
    print(f"valid organization numbers: {manifest['valid_unique_company_numbers']}")
    print(f"invalid records: {manifest['invalid_records']}")
    print(f"duplicate records: {manifest['duplicate_records']}")
    print(f"output: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
