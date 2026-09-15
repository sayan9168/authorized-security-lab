from __future__ import annotations

import hashlib
import json
import threading
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True, slots=True)
class AuditEntry:
    sequence: int
    timestamp: str
    actor: str
    action: str
    outcome: str
    details: dict[str, object]
    previous_hash: str
    entry_hash: str


class AuditChain:
    """Tamper-evident hash chain for security assessment audit events."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._entries: list[AuditEntry] = []

    def append(self, actor: str, action: str, outcome: str, details: dict[str, object] | None = None) -> AuditEntry:
        with self._lock:
            previous = self._entries[-1].entry_hash if self._entries else "0" * 64
            sequence = len(self._entries) + 1
            timestamp = datetime.now(timezone.utc).isoformat()
            payload = {
                "sequence": sequence,
                "timestamp": timestamp,
                "actor": actor,
                "action": action,
                "outcome": outcome,
                "details": details or {},
                "previous_hash": previous,
            }
            digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            entry = AuditEntry(sequence, timestamp, actor, action, outcome, payload["details"], previous, digest)
            self._entries.append(entry)
            return entry

    def verify(self) -> bool:
        with self._lock:
            previous = "0" * 64
            for entry in self._entries:
                payload = {
                    "sequence": entry.sequence,
                    "timestamp": entry.timestamp,
                    "actor": entry.actor,
                    "action": entry.action,
                    "outcome": entry.outcome,
                    "details": entry.details,
                    "previous_hash": entry.previous_hash,
                }
                expected = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
                if entry.previous_hash != previous or entry.entry_hash != expected:
                    return False
                previous = entry.entry_hash
            return True

    def entries(self) -> tuple[AuditEntry, ...]:
        with self._lock:
            return tuple(self._entries)
