from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from aslab.core.models import Option, Result


class Module(ABC):
    """Stable extension contract for safe assessment modules."""

    name: str = "Unnamed"
    author: str = "SAYANOX"
    description: str = ""
    options: dict[str, Option] = {}

    def __init__(self) -> None:
        self.options = {
            key: Option(
                name=value.name,
                description=value.description,
                required=value.required,
                default=value.default,
                value=value.value,
            )
            for key, value in self.options.items()
        }

    def set_option(self, name: str, value: str) -> None:
        key = name.upper()
        if key not in self.options:
            raise KeyError(f"Unknown option: {name}")
        self.options[key].value = value

    def validate(self) -> list[str]:
        missing = [o.name for o in self.options.values() if o.required and not o.value]
        return missing

    def option_values(self) -> dict[str, str]:
        return {key: option.value for key, option in self.options.items()}

    @abstractmethod
    def run(self) -> Result:
        """Execute a bounded assessment action and return a structured result."""
        raise NotImplementedError
