from __future__ import annotations

from dataclasses import dataclass, field
from ipaddress import ip_address, ip_network
from typing import Iterable


class PolicyViolation(ValueError):
    """Raised when an assessment request violates the active safety policy."""


@dataclass(frozen=True)
class Policy:
    allowed_networks: tuple[str, ...] = ("127.0.0.0/8", "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16")
    max_ports: int = 128
    max_workers: int = 32
    max_timeout: float = 5.0
    allowed_transports: tuple[str, ...] = ("tcp", "tls")
    require_authorized: bool = True
    denied_actions: frozenset[str] = frozenset({"exec", "credential_access", "persistence", "payload_delivery", "exploit_delivery"})

    def validate_target(self, target: str) -> None:
        try:
            address = ip_address(target)
        except ValueError as exc:
            raise PolicyViolation(f"Invalid IP target: {target}") from exc
        if not any(address in ip_network(net) for net in self.allowed_networks):
            raise PolicyViolation(f"Target {target} is outside the configured assessment networks")

    def validate_ports(self, ports: Iterable[int]) -> list[int]:
        result = list(ports)
        if not result or len(result) > self.max_ports:
            raise PolicyViolation(f"Port count must be between 1 and {self.max_ports}")
        if any(port < 1 or port > 65535 for port in result):
            raise PolicyViolation("Ports must be in the range 1..65535")
        return result

    def validate_execution(self, action: str, *, authorized: bool = False) -> None:
        if self.require_authorized and not authorized:
            raise PolicyViolation("An explicit authorization flag is required")
        if action in self.denied_actions:
            raise PolicyViolation(f"Action '{action}' is prohibited by policy")

    def validate_runtime(self, workers: int, timeout: float) -> None:
        if workers < 1 or workers > self.max_workers:
            raise PolicyViolation(f"Workers must be between 1 and {self.max_workers}")
        if timeout <= 0 or timeout > self.max_timeout:
            raise PolicyViolation(f"Timeout must be > 0 and <= {self.max_timeout}s")


@dataclass
class PolicyEngine:
    policy: Policy = field(default_factory=Policy)

    def authorize(self, action: str, target: str, *, authorized: bool) -> None:
        self.policy.validate_execution(action, authorized=authorized)
        self.policy.validate_target(target)
