from __future__ import annotations

import cmd
import shlex
import threading
from typing import Any

from rich.console import Console as RichConsole
from rich.table import Table

from aslab.core.handler import SessionHandler
from aslab.core.loader import ModuleLoader
from aslab.modules.base import Module


class Console(cmd.Cmd):
    intro = "\nAuthorized Security Lab 0.1.0 — type 'help' for commands.\n"
    prompt = "asl> "

    def __init__(self) -> None:
        super().__init__()
        self.output = RichConsole()
        self.loader = ModuleLoader()
        self.loader.discover()
        self.handler = SessionHandler()
        self.current: Module | None = None
        self._run_lock = threading.Lock()

    def emptyline(self) -> None:
        return

    def do_use(self, line: str) -> None:
        """use <module> — select an assessment module."""
        name = line.strip()
        if not name:
            self.output.print("[yellow]Usage: use <module>[/yellow]")
            return
        try:
            self.current = self.loader.create(name)
            self.prompt = f"asl ({name})> "
            self.output.print(f"[green]Selected {name}[/green]")
        except KeyError as exc:
            self.output.print(f"[red]{exc}[/red]")

    def do_set(self, line: str) -> None:
        """set <option> <value> — set a module option."""
        if self.current is None:
            self.output.print("[yellow]Select a module first.[/yellow]")
            return
        try:
            parts = shlex.split(line)
            if len(parts) < 2:
                raise ValueError("Usage: set <option> <value>")
            self.current.set_option(parts[0], " ".join(parts[1:]))
        except (ValueError, KeyError) as exc:
            self.output.print(f"[red]{exc}[/red]")

    def do_show(self, line: str) -> None:
        """show options — display selected module options."""
        if line.strip() == "modules":
            table = Table(title="Modules")
            table.add_column("Name")
            for name in self.loader.names():
                table.add_row(name)
            self.output.print(table)
            return
        if line.strip() != "options" or self.current is None:
            self.output.print("[yellow]Usage: show options | show modules[/yellow]")
            return
        table = Table(title=self.current.name)
        table.add_column("Option")
        table.add_column("Required")
        table.add_column("Value")
        table.add_column("Description")
        for option in self.current.options.values():
            table.add_row(option.name, "yes" if option.required else "no", option.value or "", option.description)
        self.output.print(table)

    def do_run(self, _: str) -> None:
        """run — execute the selected bounded assessment module."""
        if self.current is None:
            self.output.print("[yellow]Select a module first.[/yellow]")
            return
        if not self._run_lock.acquire(blocking=False):
            self.output.print("[yellow]Another module run is already active.[/yellow]")
            return
        try:
            result = self.current.run()
            self.output.print(f"[{ 'green' if result.status == 'ok' else 'red' }]{result.message}[/{ 'green' if result.status == 'ok' else 'red' }]")
            if result.data:
                self.output.print_json(data=result.data)
        except Exception as exc:
            self.output.print(f"[red]Module execution failed safely: {exc}[/red]")
        finally:
            self._run_lock.release()

    do_exploit = do_run

    def do_listeners(self, _: str) -> None:
        """listeners — start the cooperative session metadata listener."""
        self.handler.start()
        self.output.print(f"[green]Listener active on {self.handler.host}:{self.handler.port}[/green]")

    def do_sessions(self, line: str) -> None:
        """sessions [-i <id>] — list sessions or inspect one session's metadata."""
        parts = shlex.split(line)
        if len(parts) == 2 and parts[0] == "-i":
            try:
                sid = int(parts[1])
            except ValueError:
                self.output.print("[red]Session ID must be an integer.[/red]")
                return
            session = self.handler.registry.get(sid)
            if session is None:
                self.output.print("[yellow]Session not found.[/yellow]")
                return
            self.output.print_json(data={"id": session.session_id, "ip": session.peer_ip, "port": session.peer_port, "hostname": session.hostname, "transport": session.transport, "age_seconds": session.age_seconds})
            return
        table = Table(title="Active Sessions")
        for col in ("ID", "IP", "Port", "Hostname", "Transport", "Age"):
            table.add_column(col)
        for session in self.handler.sessions():
            table.add_row(str(session.session_id), session.peer_ip, str(session.peer_port), session.hostname, session.transport, f"{session.age_seconds}s")
        self.output.print(table)

    def do_background(self, _: str) -> None:
        """background — return to the top-level prompt."""
        self.current = None
        self.prompt = "asl> "
        self.output.print("[cyan]Module context cleared.[/cyan]")

    def do_reload(self, _: str) -> None:
        """reload — rediscover modules from disk."""
        self.loader.discover()
        self.output.print(f"[green]Discovered {len(self.loader.names())} module(s).[/green]")

    def do_exit(self, _: str) -> bool:
        """exit — stop services and quit."""
        self.handler.stop()
        return True

    do_quit = do_exit
    do_EOF = do_exit

    def completenames(self, text: str, *ignored: Any) -> list[str]:
        names = ["use", "set", "show", "run", "exploit", "listeners", "sessions", "background", "reload", "exit", "quit"]
        return [name for name in names if name.startswith(text)]
