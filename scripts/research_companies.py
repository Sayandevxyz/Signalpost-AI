"""Checkpointed, bounded-concurrency batch research runner."""
from __future__ import annotations

import argparse
import asyncio
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from signalpost.app.agents.coordinator import ResearchCoordinator
from signalpost.app.extraction.normalizer import normalize_registration_number
from signalpost.app.sources.base import StaticRegistrySource


def load_numbers(path: Path) -> list[str]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [normalize_registration_number(row["company_number"]) for row in csv.DictReader(handle)]


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
        "research": {"status": "partial" if state.get("errors") else "complete", "errors": state.get("errors", [])},
    }


async def run(input_path: str, output_path: str, concurrency: int = 4) -> None:
    input_file, output_file = Path(input_path), Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    numbers = load_numbers(input_file)
    done = load_done(output_file)
    queue = [number for number in numbers if number not in done]
    semaphore = asyncio.Semaphore(max(1, concurrency))

    async def research(number: str) -> tuple[str, dict]:
        async with semaphore:
            coordinator = ResearchCoordinator([StaticRegistrySource()])
            for attempt in range(3):
                try:
                    return number, serialize(await coordinator.research(number))
                except Exception as exc:  # keep one company from stopping the batch
                    if attempt == 2:
                        return number, {"company": {"company_number": number}, "facts": [], "events": [], "research": {"status": "failed", "errors": [str(exc)]}}
                    await asyncio.sleep(0.25 * (2**attempt))
        raise RuntimeError("unreachable")

    results = await asyncio.gather(*(research(number) for number in queue))
    with output_file.open("a", encoding="utf-8") as handle:
        for _, profile in results:
            handle.write(json.dumps(profile, default=str, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Research Norwegian companies in a resumable batch")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--concurrency", type=int, default=4)
    args = parser.parse_args()
    asyncio.run(run(args.input, args.output, args.concurrency))
