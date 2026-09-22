"""Checkpointed, bounded-concurrency batch research runner."""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from signalpost.app.agents.coordinator import ResearchCoordinator
from signalpost.app.extraction.normalizer import normalize_registration_number
from signalpost.app.metrics import MetricsCollector, quality_metrics
from signalpost.app.sources.base import StaticRegistrySource


def load_numbers(path: Path) -> list[str]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [
            normalize_registration_number(row["company_number"]) for row in csv.DictReader(handle)
        ]


def load_done(path: Path) -> set[str]:
    if not path.exists():
        return set()
    done: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            profile = json.loads(line)
            number = profile.get("company", {}).get("company_number")
            if number:
                done.add(str(number))
        except json.JSONDecodeError:
            continue
    return done


def serialize(state: dict) -> dict:
    return {
        "company": state.get("company_identity", {}),
        "facts": state.get("verified_facts", []),
        "events": state.get("events", []),
        "research": {
            "status": "partial" if state.get("errors") else "complete",
            "errors": state.get("errors", []),
        },
    }


async def run(
    input_path: str,
    output_path: str,
    concurrency: int = 4,
    metrics_output: str | None = None,
) -> dict:
    input_file, output_file = Path(input_path), Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    numbers = load_numbers(input_file)
    done = load_done(output_file)
    queue = [number for number in numbers if number not in done]
    semaphore = asyncio.Semaphore(max(1, concurrency))
    collector = MetricsCollector()
    benchmark_started = time.perf_counter()

    async def research(number: str) -> tuple[str, dict, int]:
        async with semaphore:
            for attempt in range(3):
                started = time.perf_counter()
                coordinator = ResearchCoordinator([StaticRegistrySource()], session_factory=None)
                try:
                    state = await coordinator.research(number)
                    profile = serialize(state)
                    profile["research"]["request_count"] = state.get("request_count", 0)
                    profile["research"]["llm_calls"] = state.get("llm_calls", 0)
                    collector.record(profile, time.perf_counter() - started, attempt)
                    return number, profile, attempt
                except Exception as exc:  # noqa: BLE001 - isolate failures per company
                    if attempt == 2:
                        profile = {
                            "company": {"company_number": number},
                            "facts": [],
                            "events": [],
                            "research": {"status": "failed", "errors": [str(exc)]},
                        }
                        collector.record(profile, time.perf_counter() - started, attempt)
                        return number, profile, attempt
                    await asyncio.sleep(0.25 * (2**attempt))
        raise RuntimeError("unreachable")

    results = await asyncio.gather(*(research(number) for number in queue))
    lines = [
        json.dumps(profile, default=str, ensure_ascii=False) + "\n" for _, profile, _ in results
    ]

    def append_lines() -> None:
        with output_file.open("a", encoding="utf-8") as handle:
            handle.writelines(lines)

    await asyncio.to_thread(append_lines)
    elapsed = time.perf_counter() - benchmark_started
    metrics = collector.as_dict(len(numbers), elapsed, bool(done), 1 if queue else 0)
    existing_profiles = [
        json.loads(line)
        for line in output_file.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    metrics["quality"] = quality_metrics(existing_profiles)
    if metrics_output:
        metrics_path = Path(metrics_output)
        metrics_path.parent.mkdir(parents=True, exist_ok=True)
        metrics_path.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Research Norwegian companies in a resumable batch"
    )
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--metrics-output", help="Write measured benchmark metrics JSON")
    args = parser.parse_args()
    asyncio.run(run(args.input, args.output, args.concurrency, args.metrics_output))
