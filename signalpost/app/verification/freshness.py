from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


class FreshnessChecker:
    def choose_current(self, facts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        grouped: dict[str, list[dict[str, Any]]] = {}
        for fact in facts:
            grouped.setdefault(fact["field"], []).append(fact)
        result = []
        for items in grouped.values():
            items.sort(
                key=lambda x: x.get("published_at") or x.get("retrieved_at") or "", reverse=True
            )
            for index, item in enumerate(items):
                item["is_current"] = index == 0
                result.append(item)
        return result

    def mark(self, old: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
        old["is_current"] = False
        new["is_current"] = True
        new.setdefault("first_seen_at", old.get("first_seen_at", datetime.now(timezone.utc)))
        return new
