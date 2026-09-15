from __future__ import annotations

import importlib
import pkgutil
import threading
from types import ModuleType
from typing import Type

from aslab.modules.base import Module


class ModuleLoader:
    """Thread-safe module discovery with reload support."""

    def __init__(self, package: str = "aslab.modules") -> None:
        self.package = package
        self._lock = threading.RLock()
        self._modules: dict[str, Type[Module]] = {}
        self._loaded: dict[str, ModuleType] = {}

    def discover(self) -> list[str]:
        with self._lock:
            package = importlib.import_module(self.package)
            prefix = package.__name__ + "."
            for info in pkgutil.walk_packages(package.__path__, prefix):
                if info.name.endswith(".base") or info.name.endswith(".__init__"):
                    continue
                self._load_module(info.name, reload_existing=False)
            return sorted(self._modules)

    def _load_module(self, module_name: str, reload_existing: bool) -> None:
        try:
            module = importlib.import_module(module_name)
            if reload_existing:
                module = importlib.reload(module)
            found: list[Type[Module]] = []
            for value in vars(module).values():
                if isinstance(value, type) and issubclass(value, Module) and value is not Module:
                    found.append(value)
            for cls in found:
                self._modules[cls.name] = cls
            self._loaded[module_name] = module
        except (ImportError, AttributeError, TypeError) as exc:
            raise RuntimeError(f"Could not load module {module_name}: {exc}") from exc

    def reload(self, name: str) -> None:
        with self._lock:
            module_name = next(
                (module_name for module_name, module in self._loaded.items() if any(
                    getattr(value, "name", None) == name for value in vars(module).values()
                )),
                None,
            )
            if module_name is None:
                raise KeyError(name)
            self._modules = {key: value for key, value in self._modules.items() if value.__module__ != module_name}
            self._load_module(module_name, reload_existing=True)

    def create(self, name: str) -> Module:
        with self._lock:
            if name not in self._modules:
                self.discover()
            if name not in self._modules:
                raise KeyError(f"Module not found: {name}")
            return self._modules[name]()

    def names(self) -> list[str]:
        with self._lock:
            return sorted(self._modules)
