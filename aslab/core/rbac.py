from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Role(StrEnum):
    ADMIN = "admin"
    OPERATOR = "operator"
    AUDITOR = "auditor"
    VIEWER = "viewer"


PERMISSIONS: dict[Role, frozenset[str]] = {
    Role.ADMIN: frozenset({"read", "run", "manage_users", "manage_modules", "export"}),
    Role.OPERATOR: frozenset({"read", "run", "export"}),
    Role.AUDITOR: frozenset({"read", "export"}),
    Role.VIEWER: frozenset({"read"}),
}


@dataclass(frozen=True)
class Principal:
    username: str
    role: Role

    def can(self, permission: str) -> bool:
        return permission in PERMISSIONS[self.role]

    def require(self, permission: str) -> None:
        if not self.can(permission):
            raise PermissionError(f"Role '{self.role.value}' lacks permission '{permission}'")
