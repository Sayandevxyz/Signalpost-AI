# Signalpost Requirements Matrix

| Requirement | Status | Evidence |
| --- | --- | --- |
| 1,000+ company profiles | Partial | `data/output/profiles-1000.jsonl` contains exactly 1,000 completed records; 84 contain verified facts and 916 are zero-fact records. |
| Repository | Verified | `https://github.com/Sayandevxyz/Signalpost-AI` |
| Exact commit | Not validated in this run | Use `git rev-parse HEAD` after the final reviewed commit. |
| One-command run | Partial | Batch runner and benchmark scripts exist; a fully production-backed one-command deployment was not validated. |
| Model/API details | Partial | Pydantic, SQLAlchemy, FastAPI, and LangGraph dependencies are declared; provider-backed LLM extraction is not validated. |
| Expected run costs | Not available | The selected benchmark used no LLM provider and does not expose measured provider cost. |
| Identity verification | Partial | Registry identity fields are emitted and evidence verification exists; wrong-company coverage is not fully validated against live sources. |
| Evidence | Partial | 84/84 extracted facts have evidence in the benchmark artifact; source metadata completeness is not fully validated. |
| Freshness | Implemented, not fully validated | Freshness module and tests exist; production multi-source history validation is pending. |
| Batch processing | Verified locally | Checkpointed JSONL batch runner, retries, and duplicate prevention are implemented. |
| PostgreSQL | Not validated | SQLAlchemy configuration supports PostgreSQL URLs; no PostgreSQL runtime was available. |
| Redis | Not validated | Redis dependency and Compose service are present; Redis executable was unavailable locally. |
| Docker | Not validated | Docker executable was unavailable locally; files were inspected statically. |
| Tests and lint | Verified locally | Python 3.13 environment previously collected and passed 13 tests; rerun after final changes is required. |
| Benchmark diagnostics | Verified locally | `scripts/benchmark_diagnostics.py` writes JSON and text reports with per-record zero-fact reasons. |
