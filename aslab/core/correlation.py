from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True, slots=True)
class Correlation:
    asset: str
    finding_ids: tuple[str, ...]
    score: float


class CorrelationEngine:
    """Correlates assessment findings by normalized asset identity and tags."""

    def correlate(self, findings: Iterable[dict[str, object]]) -> tuple[Correlation, ...]:
        groups: dict[str, list[str]] = defaultdict(list)
        for finding in findings:
            asset = str(finding.get("asset", "unknown"))
            finding_id = str(finding.get("id", ""))
            if finding_id:
                groups[asset].append(finding_id)
        result = []
        for asset, ids in groups.items():
            score = min(1.0, len(ids) / 10.0)
            result.append(Correlation(asset, tuple(ids), score))
        return tuple(result)
