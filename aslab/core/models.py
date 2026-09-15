from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class Option:
    name: str
    description: str
    required: bool = False
    default: str = ""
    value: str = ""

    def __post_init__(self) -> None:
        if not self.value:
            self.value = self.default


@dataclass(slots=True)
class Result:
    status: str
    message: str
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(slots=True)
class Session:
    session_id: int
    peer_ip: str
    peer_port: int
    hostname: str
    connected_at: datetime
    socket: Any = field(repr=False)
    transport: str = "tcp"

    @property
    def age_seconds(self) -> int:
        return max(0, int((datetime.now(timezone.utc) - self.connected_at).total_seconds()))
