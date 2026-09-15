from __future__ import annotations

import ipaddress
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Iterable

from aslab.core.models import Option, Result
from aslab.modules.base import Module


class PortScan(Module):
    name = "scanner/port_scan"
    author = "SAYANOX"
    description = "Bounded TCP connect audit for explicitly authorized assets."
    options = {
        "RHOST": Option("RHOST", "IPv4/IPv6 address or hostname to audit", True),
        "PORTS": Option("PORTS", "Comma-separated TCP ports", False, "22,80,443,8080"),
        "TIMEOUT": Option("TIMEOUT", "Per-connection timeout in seconds", False, "0.75"),
        "WORKERS": Option("WORKERS", "Maximum concurrent connection checks", False, "32"),
    }

    @staticmethod
    def _ports(raw: str) -> list[int]:
        ports: set[int] = set()
        for token in raw.split(","):
            token = token.strip()
            if not token:
                continue
            if "-" in token:
                left, right = token.split("-", 1)
                start, end = int(left), int(right)
                if start > end:
                    raise ValueError("PORTS range must be ascending")
                ports.update(range(start, end + 1))
            else:
                ports.add(int(token))
        if not ports or any(p < 1 or p > 65535 for p in ports):
            raise ValueError("PORTS must contain values from 1 to 65535")
        if len(ports) > 1024:
            raise ValueError("PORTS is limited to 1024 entries per run")
        return sorted(ports)

    def run(self) -> Result:
        values = self.option_values()
        missing = self.validate()
        if missing:
            return Result("error", f"Missing required options: {', '.join(missing)}")

        host = values["RHOST"].strip()
        try:
            address = ipaddress.ip_address(host)
            if address.is_unspecified or address.is_multicast:
                return Result("error", "RHOST must be a specific unicast address")
        except ValueError:
            try:
                host = socket.gethostbyname(host)
            except socket.gaierror as exc:
                return Result("error", f"Unable to resolve RHOST: {exc}")

        try:
            ports = self._ports(values["PORTS"])
            timeout = float(values["TIMEOUT"])
            workers = int(values["WORKERS"])
            if not 0.05 <= timeout <= 10:
                raise ValueError("TIMEOUT must be between 0.05 and 10 seconds")
            if not 1 <= workers <= 128:
                raise ValueError("WORKERS must be between 1 and 128")
        except ValueError as exc:
            return Result("error", str(exc))

        def check(port: int) -> tuple[int, bool, str]:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            try:
                code = sock.connect_ex((host, port))
                return port, code == 0, "open" if code == 0 else "closed"
            except OSError as exc:
                return port, False, f"error: {exc}"
            finally:
                sock.close()

        results: list[tuple[int, bool, str]] = []
        with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="audit") as pool:
            futures = [pool.submit(check, port) for port in ports]
            for future in as_completed(futures):
                results.append(future.result())

        results.sort()
        open_ports = [port for port, is_open, _ in results if is_open]
        return Result(
            "ok",
            f"Audit complete: {len(open_ports)} open TCP port(s) found on {host}.",
            {"host": host, "open_ports": open_ports, "checked": len(results)},
        )
