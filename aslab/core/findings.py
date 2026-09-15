from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


SEVERITIES = ("info", "low", "medium", "high", "critical")


@dataclass(slots=True)
class Finding:
    title: str
    severity: str
    asset: str
    description: str
    evidence: dict[str, Any] = field(default_factory=dict)
    remediation: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self) -> None:
        self.severity = self.severity.lower()
        if self.severity not in SEVERITIES:
            raise ValueError(f"Invalid severity: {self.severity}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class FindingStore:
    def __init__(self) -> None:
        self._items: list[Finding] = []

    def add(self, finding: Finding) -> None:
        self._items.append(finding)

    def all(self) -> list[Finding]:
        return list(self._items)

    def by_severity(self, severity: str) -> list[Finding]:
        severity = severity.lower()
        return [item for item in self._items if item.severity == severity]

    def summary(self) -> dict[str, int]:
        return {severity: len(self.by_severity(severity)) for severity in SEVERITIES}
