from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import RLock
from typing import Any, Callable
from uuid import uuid4


@dataclass(frozen=True)
class Event:
    type: str
    data: dict[str, Any]
    event_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class EventBus:
    def __init__(self) -> None:
        self._lock = RLock()
        self._subscribers: dict[str, list[Callable[[Event], None]]] = {}
        self._wildcards: list[Callable[[Event], None]] = []

    def subscribe(self, event_type: str, callback: Callable[[Event], None]) -> None:
        with self._lock:
            self._subscribers.setdefault(event_type, []).append(callback)

    def subscribe_all(self, callback: Callable[[Event], None]) -> None:
        with self._lock:
            self._wildcards.append(callback)

    def publish(self, event_type: str, **data: Any) -> Event:
        event = Event(event_type, data)
        with self._lock:
            callbacks = tuple(self._subscribers.get(event_type, ())) + tuple(self._wildcards)
        for callback in callbacks:
            try:
                callback(event)
            except Exception:
                continue
        return event
