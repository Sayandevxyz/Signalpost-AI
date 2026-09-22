"""Signalpost command-line interface."""

from __future__ import annotations

import argparse
import asyncio
import json

from ..agents.coordinator import ResearchCoordinator
from ..extraction.normalizer import normalize_registration_number
from ..sources.base import StaticRegistrySource


def render(profile: dict) -> str:
    company = profile.get("company", {})
    research = profile.get("research", {})
    return "\n".join(
        [
            "Signalpost AI",
            "=" * 48,
            f"Company: {company.get('legal_name') or 'Not found'}",
            f"Registration number: {company.get('company_number')}",
            f"Status: {company.get('status') or 'not_found'}",
            f"Website: {company.get('website') or 'not_found'}",
            f"Verified facts: {len(profile.get('facts', []))}",
            f"Evidence: {sum(bool(f.get('evidence') or f.get('source_url')) for f in profile.get('facts', []))} fact sources",
            f"Research status: {research.get('status', 'unknown')}",
            *(f"Error: {error}" for error in research.get("errors", [])),
        ]
    )


async def research(number: str) -> dict:
    coordinator = ResearchCoordinator([StaticRegistrySource()])
    state = await coordinator.research(normalize_registration_number(number))
    return {
        "company": state.get("company_identity", {}),
        "facts": state.get("verified_facts", []),
        "events": state.get("events", []),
        "research": {
            "status": "partial" if state.get("errors") else "complete",
            "errors": state.get("errors", []),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(prog="signalpost")
    sub = parser.add_subparsers(dest="command", required=True)
    command = sub.add_parser("research", help="Research one company")
    command.add_argument("company_number")
    command.add_argument("--json", action="store_true")
    batch = sub.add_parser("batch", help="Research companies from CSV")
    batch.add_argument("input")
    batch.add_argument("--output", default="data/output/profiles.jsonl")
    batch.add_argument("--concurrency", type=int, default=4)
    args = parser.parse_args()
    if args.command == "research":
        try:
            profile = asyncio.run(research(args.company_number))
        except ValueError as exc:
            parser.error(str(exc))
        print(json.dumps(profile, indent=2, default=str) if args.json else render(profile))
    else:
        from scripts.research_companies import run

        asyncio.run(run(args.input, args.output, args.concurrency))
        print(f"Wrote batch profiles to {args.output}")


if __name__ == "__main__":
    main()
