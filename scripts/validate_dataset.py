import json
import re
import sys
from pathlib import Path

NUMBER_PATTERN = re.compile(r"^[0-9]{9}$")
DEFAULT_PATH = Path("data/input/norwegian_companies.jsonl")


def validate(path: Path) -> dict[str, object]:
    total = valid = duplicates = invalid = 0
    seen: set[str] = set()
    errors: list[dict[str, object]] = []
    if not path.exists():
        return {
            "path": str(path),
            "total": 0,
            "valid": 0,
            "duplicates": 0,
            "invalid": 0,
            "errors": [{"line": 0, "error": "file_not_found"}],
        }

    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw_line.strip():
            continue
        total += 1
        try:
            record = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            invalid += 1
            errors.append({"line": line_number, "error": f"invalid_json: {exc.msg}"})
            continue
        number = record.get("company_number") if isinstance(record, dict) else None
        number = str(number).strip() if number is not None else ""
        if not NUMBER_PATTERN.fullmatch(number):
            invalid += 1
            errors.append({"line": line_number, "error": "company_number_must_be_9_digits"})
            continue
        if number in seen:
            duplicates += 1
            invalid += 1
            errors.append(
                {"line": line_number, "error": "duplicate_company_number", "company_number": number}
            )
            continue
        seen.add(number)
        valid += 1

    return {
        "path": str(path),
        "total": total,
        "valid": valid,
        "duplicates": duplicates,
        "invalid": invalid,
        "errors": errors,
    }


if __name__ == "__main__":
    report = validate(Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PATH)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if report["total"] == 0 or report["invalid"]:
        raise SystemExit(1)
