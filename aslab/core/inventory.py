from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone


@dataclass(slots=True)
class Asset:
    asset_id: str
    address: str
    hostname: str = ""
    tags: set[str] = field(default_factory=set)
    first_seen: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_seen: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def touch(self) -> None:
        self.last_seen = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        data = asdict(self)
        data["tags"] = sorted(self.tags)
        return data


class AssetInventory:
    def __init__(self) -> None:
        self._assets: dict[str, Asset] = {}

    def upsert(self, asset: Asset) -> Asset:
        existing = self._assets.get(asset.asset_id)
        if existing is None:
            self._assets[asset.asset_id] = asset
            return asset
        existing.address = asset.address
        existing.hostname = asset.hostname or existing.hostname
        existing.tags.update(asset.tags)
        existing.touch()
        return existing

    def get(self, asset_id: str) -> Asset | None:
        return self._assets.get(asset_id)

    def all(self) -> list[Asset]:
        return list(self._assets.values())

    def tagged(self, tag: str) -> list[Asset]:
        return [asset for asset in self._assets.values() if tag in asset.tags]
