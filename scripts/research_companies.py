import argparse
import asyncio
import csv
import json
from pathlib import Path

from signalpost.app.agents.coordinator import ResearchCoordinator
from signalpost.app.sources.base import StaticRegistrySource


async def run(input_path: str, output_path: str):
    numbers = [row["company_number"] for row in csv.DictReader(Path(input_path).open())]
    done = {json.loads(line)["company"]["company_number"] for line in Path(output_path).read_text().splitlines()} if Path(output_path).exists() else set()
    coordinator = ResearchCoordinator([StaticRegistrySource()])
    with Path(output_path).open("a") as out:
        for number in numbers:
            if number in done: continue
            state = await coordinator.research(number)
            out.write(json.dumps({"company": state.get("company_identity", {}), "facts": state.get("verified_facts", []), "events": state.get("events", []), "research": {"errors": state["errors"]}}, default=str) + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--input", required=True); parser.add_argument("--output", required=True)
    args = parser.parse_args(); asyncio.run(run(args.input, args.output))
