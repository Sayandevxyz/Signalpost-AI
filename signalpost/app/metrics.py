"""Lightweight, observational benchmark metrics."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


def percentile(values: list[float], percentile_value: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    rank = (len(ordered) - 1) * percentile_value / 100
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (rank - lower)


@dataclass
class MetricsCollector:
    latencies: list[float] = field(default_factory=list)
    processed: int = 0
    complete: int = 0
    partial: int = 0
    failed: int = 0
    requests: int = 0
    llm_calls: int = 0
    retries: int = 0
    timeouts: int = 0
    rate_limits: int = 0
    http_errors: int = 0
    connection_errors: int = 0
    other_failures: int = 0
    input_tokens: int | None = None
    output_tokens: int | None = None
    provider: str | None = None
    model: str | None = None

    def record(self, profile: dict[str, Any], latency: float, retries: int = 0) -> None:
        self.latencies.append(latency)
        self.processed += 1
        status = profile.get("research", {}).get("status")
        if status == "complete":
            self.complete += 1
        elif status == "partial":
            self.partial += 1
        else:
            self.failed += 1
        self.requests += int(profile.get("research", {}).get("request_count", 0))
        self.llm_calls += int(profile.get("research", {}).get("llm_calls", 0))
        self.retries += retries
        for error in profile.get("research", {}).get("errors", []):
            text = str(error).lower()
            if "timeout" in text:
                self.timeouts += 1
            elif "rate limit" in text or "429" in text:
                self.rate_limits += 1
            elif "http" in text or "status code" in text:
                self.http_errors += 1
            elif "connect" in text:
                self.connection_errors += 1
            else:
                self.other_failures += 1

    def as_dict(
        self, requested: int, elapsed_seconds: float, resumed: bool, checkpoints: int
    ) -> dict[str, Any]:
        values = self.latencies
        average = sum(values) / len(values) if values else None
        return {
            "benchmark": {
                "requested": requested,
                "processed": self.processed,
                "complete": self.complete,
                "partial": self.partial,
                "failed": self.failed,
            },
            "latency": {
                "elapsed_seconds": elapsed_seconds,
                "average_seconds": average,
                "p50_seconds": percentile(values, 50),
                "p95_seconds": percentile(values, 95),
                "p99_seconds": percentile(values, 99),
                "min_seconds": min(values) if values else None,
                "max_seconds": max(values) if values else None,
            },
            "throughput": {
                "companies_per_second": self.processed / elapsed_seconds
                if elapsed_seconds > 0
                else None,
                "companies_per_minute": self.processed * 60 / elapsed_seconds
                if elapsed_seconds > 0
                else None,
            },
            "requests": {
                "total": self.requests,
                "per_company": self.requests / self.processed if self.processed else None,
                "by_source": {},
            },
            "llm": {
                "calls": self.llm_calls,
                "calls_per_company": self.llm_calls / self.processed if self.processed else None,
                "provider": self.provider,
                "model": self.model,
                "tokens": None,
                "tokens_available": False,
            },
            "cost": {"amount": None, "currency": None, "available": False},
            "errors": {
                "retries": self.retries,
                "timeouts": self.timeouts,
                "rate_limits": self.rate_limits,
                "http_errors": self.http_errors,
                "connection_errors": self.connection_errors,
                "other_failures": self.other_failures,
            },
            "checkpoint": {
                "enabled": True,
                "resumed": resumed,
                "checkpoints": checkpoints,
                "initial_records": requested,
                "resumed_records": requested - self.processed,
            },
        }


def quality_metrics(profiles: list[dict[str, Any]]) -> dict[str, Any]:
    facts = [fact for profile in profiles for fact in profile.get("facts", [])]
    records_with_facts = sum(bool(profile.get("facts")) for profile in profiles)
    evidenced = sum(
        bool(fact.get("evidence") or fact.get("quoted_evidence") or fact.get("source_url"))
        for fact in facts
    )
    return {
        "records_with_facts": records_with_facts,
        "zero_fact_records": len(profiles) - records_with_facts,
        "facts": len(facts),
        "evidence_coverage": evidenced / len(facts) if facts else 0.0,
    }


def empty_metrics() -> dict[str, Any]:
    return MetricsCollector().as_dict(0, 0.0, False, 0)


__all__ = ["MetricsCollector", "empty_metrics", "percentile", "quality_metrics"]
