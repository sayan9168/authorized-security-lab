from __future__ import annotations

import secrets
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable


@dataclass(frozen=True, slots=True)
class ApiKeyRecord:
    key_id: str
    token: str
    role: str
    created_at: datetime
    enabled: bool = True


class ApiKeyStore:
    """In-memory API-key registry; persist only hashed tokens in production."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._keys: dict[str, ApiKeyRecord] = {}

    def create(self, role: str) -> tuple[str, ApiKeyRecord]:
        key_id = secrets.token_hex(8)
        token = secrets.token_urlsafe(32)
        record = ApiKeyRecord(key_id, token, role, datetime.now(timezone.utc))
        with self._lock:
            self._keys[key_id] = record
        return token, record

    def authenticate(self, token: str) -> ApiKeyRecord | None:
        with self._lock:
            for record in self._keys.values():
                if record.enabled and secrets.compare_digest(record.token, token):
                    return record
        return None

    def revoke(self, key_id: str) -> bool:
        with self._lock:
            record = self._keys.get(key_id)
            if record is None:
                return False
            self._keys[key_id] = ApiKeyRecord(record.key_id, record.token, record.role, record.created_at, False)
            return True


class RateLimiter:
    """Simple per-key fixed-window limiter for local API use."""

    def __init__(self, limit: int = 60, window_seconds: int = 60) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._lock = threading.RLock()
        self._windows: dict[str, tuple[int, int]] = {}

    def allow(self, identity: str, now: int) -> bool:
        with self._lock:
            start, count = self._windows.get(identity, (now, 0))
            if now - start >= self.window_seconds:
                start, count = now, 0
            if count >= self.limit:
                self._windows[identity] = (start, count)
                return False
            self._windows[identity] = (start, count + 1)
            return True


@dataclass(frozen=True, slots=True)
class Route:
    method: str
    path: str
    handler: Callable[..., object]
    permission: str


class ApiRouter:
    def __init__(self) -> None:
        self._routes: dict[tuple[str, str], Route] = {}

    def add(self, method: str, path: str, handler: Callable[..., object], permission: str = "read") -> None:
        self._routes[(method.upper(), path)] = Route(method.upper(), path, handler, permission)

    def resolve(self, method: str, path: str) -> Route | None:
        return self._routes.get((method.upper(), path))
