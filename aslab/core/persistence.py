from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any


class JsonStore:
    """Atomic, local JSON store for auditable framework state."""

    def __init__(self, path: str | Path = ".aslab/state.json") -> None:
        self.path = Path(path)
        self._lock = threading.RLock()

    def read(self) -> dict[str, Any]:
        with self._lock:
            if not self.path.exists():
                return {}
            try:
                value = json.loads(self.path.read_text(encoding="utf-8"))
                return value if isinstance(value, dict) else {}
            except (OSError, json.JSONDecodeError):
                return {}

    def write(self, value: dict[str, Any]) -> None:
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.path.with_suffix(".tmp")
            temporary.write_text(json.dumps(value, indent=2, sort_keys=True), encoding="utf-8")
            temporary.replace(self.path)
