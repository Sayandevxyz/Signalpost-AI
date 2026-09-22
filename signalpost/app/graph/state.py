from datetime import datetime
from typing import Any, TypedDict


class ResearchState(TypedDict, total=False):
    company_number: str
    company_identity: dict[str, Any]
    source_documents: list[dict[str, Any]]
    candidate_facts: list[dict[str, Any]]
    verified_facts: list[dict[str, Any]]
    rejected_facts: list[dict[str, Any]]
    events: list[dict[str, Any]]
    errors: list[str]
    request_count: int
    search_count: int
    estimated_cost: float
    input_tokens: int
    output_tokens: int
    llm_calls: int
    failed_requests: int
    retry_count: int
    request_durations: list[float]
    conflicts: list[dict[str, Any]]
    started_at: datetime
    finished_at: datetime
