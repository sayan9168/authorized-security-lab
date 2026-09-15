from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from aslab.core.events import EventBus
from aslab.core.policy import PolicyEngine, PolicyViolation


@dataclass(frozen=True)
class ScenarioStep:
    name: str
    action: str
    target: str
    execute: Callable[[], object]


class SafeBASRunner:
    """Runs explicitly approved, non-destructive validation scenarios."""

    def __init__(self, policy: PolicyEngine, events: EventBus) -> None:
        self.policy = policy
        self.events = events

    def run(self, scenario: str, steps: list[ScenarioStep], *, authorized: bool) -> list[object]:
        results: list[object] = []
        self.events.publish("scenario.started", scenario=scenario)
        try:
            for step in steps:
                self.policy.authorize(step.action, step.target, authorized=authorized)
                self.events.publish("scenario.step.started", scenario=scenario, step=step.name)
                try:
                    result = step.execute()
                    results.append(result)
                    self.events.publish("scenario.step.completed", scenario=scenario, step=step.name)
                except Exception as exc:
                    self.events.publish("scenario.step.failed", scenario=scenario, step=step.name, error=str(exc))
            self.events.publish("scenario.completed", scenario=scenario)
            return results
        except PolicyViolation as exc:
            self.events.publish("scenario.blocked", scenario=scenario, reason=str(exc))
            raise
