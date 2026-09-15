from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ModuleManifest:
    name: str
    version: str
    sha256: str
    capabilities: tuple[str, ...]

    def canonical(self) -> bytes:
        payload = {"name": self.name, "version": self.version, "sha256": self.sha256, "capabilities": list(self.capabilities)}
        return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()


class ManifestVerifier:
    def __init__(self, signing_key: bytes) -> None:
        if len(signing_key) < 32:
            raise ValueError("Signing key must contain at least 32 bytes")
        self._key = signing_key

    def sign(self, manifest: ModuleManifest) -> str:
        return hmac.new(self._key, manifest.canonical(), hashlib.sha256).hexdigest()

    def verify(self, manifest: ModuleManifest, signature: str) -> bool:
        expected = self.sign(manifest)
        return hmac.compare_digest(expected, signature)


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
