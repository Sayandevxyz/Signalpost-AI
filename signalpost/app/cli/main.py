import argparse
import asyncio
import json

from ..agents.coordinator import ResearchCoordinator
from ..extraction.normalizer import normalize_registration_number
from ..sources.base import StaticRegistrySource


def main():
    parser = argparse.ArgumentParser(prog="signalpost")
    sub = parser.add_subparsers(dest="command", required=True)
    research = sub.add_parser("research"); research.add_argument("company_number"); research.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.command == "research":
        number = normalize_registration_number(args.company_number)
        state = asyncio.run(ResearchCoordinator([StaticRegistrySource()]).research(number))
        output = {"company": state.get("company_identity", {}), "facts": state.get("verified_facts", []), "events": state.get("events", []), "research": {"status": "partial" if state["errors"] else "complete", "errors": state["errors"]}}
        print(json.dumps(output, indent=2, default=str) if args.json else f"Signalpost AI\\nCompany number: {number}\\nStatus: {output['research']['status']}")
if __name__ == "__main__": main()
