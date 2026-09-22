import json
from pathlib import Path

p=Path("data/output/profiles.jsonl")
rows=[json.loads(x) for x in p.read_text().splitlines()] if p.exists() else []
result={"companies_processed":len(rows),"success_rate":sum(not r.get("research",{}).get("errors") for r in rows)/len(rows) if rows else 0,"evidence_rate":sum(bool(f.get("evidence")) for r in rows for f in r.get("facts",[]))/max(1,sum(len(r.get("facts",[])) for r in rows))}
Path("data/output/benchmark.json").write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
