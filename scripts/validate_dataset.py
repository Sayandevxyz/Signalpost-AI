import json
import sys
from pathlib import Path

path = Path(sys.argv[1] if len(sys.argv) > 1 else "data/output/company_profiles.jsonl")
valid = total = 0
if path.exists():
    for line in path.read_text().splitlines():
        total += 1
        try:
            profile = json.loads(line)
            facts = profile.get("facts", [])
            if all(f.get("evidence") for f in facts): valid += 1
        except json.JSONDecodeError: pass
print(f"Dataset validation  Companies: {total} Valid: {valid} Invalid: {total-valid}")
