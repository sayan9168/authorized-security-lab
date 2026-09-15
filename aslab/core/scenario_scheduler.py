from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable


@dataclass(frozen=True, slots=True)
class ScheduledScenario:
    scenario_id: str
    run_at: float
    action: Callable[[], object]
    enabled: bool = True


class ScenarioScheduler:
    """Small local scheduler for pre-approved, non-destructive BAS scenarios."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._items: list[ScheduledScenario] = []

    def schedule(self, scenario_id: str, run_at: datetime, action: Callable[[], object]) -> None:
        if run_at.tzinfo is None:
            raise ValueError("run_at must be timezone-aware")
        with self._lock:
            self._items.append(ScheduledScenario(scenario_id, run_at.timestamp(), action))

    def due(self, now: float | None = None) -> tuple[ScheduledScenario, ...]:
        current = time.time() if now is None else now
        with self._lock:
            due_items = tuple(item for item in self._items if item.enabled and item.run_at <= current)
            self._items = [item for item in self._items if item not in due_items]
            return due_items

    def run_due(self, now: float | None = None) -> list[object]:
        results: list[object] = []
        for item in self.due(now):
            results.append(item.action())
        return results
