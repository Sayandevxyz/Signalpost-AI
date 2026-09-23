from __future__ import annotations

from datetime import datetime, timezone

from ..agents.coordinator import ResearchCoordinator
from ..graph.state import ResearchState


class ResearchGraph:
    def __init__(self, coordinator: ResearchCoordinator | None = None):
        self.coordinator = coordinator or ResearchCoordinator()

    async def execute(self, company_number: str) -> ResearchState:
        state = await self.coordinator.research(company_number)
        state.setdefault("started_at", datetime.now(timezone.utc))
        state.setdefault("finished_at", datetime.now(timezone.utc))
        return state


async def execute_research(company_number: str) -> ResearchState:
    return await ResearchGraph().execute(company_number)
