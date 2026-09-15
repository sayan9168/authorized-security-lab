from __future__ import annotations

import asyncio
import json
import logging
import ssl
import threading
from datetime import datetime, timezone
from typing import Callable

from aslab.core.models import Session


class SessionRegistry:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._sessions: dict[int, Session] = {}
        self._next_id = 1

    def add(self, session: Session) -> int:
        with self._lock:
            session.session_id = self._next_id
            self._next_id += 1
            self._sessions[session.session_id] = session
            return session.session_id

    def remove(self, session_id: int) -> Session | None:
        with self._lock:
            return self._sessions.pop(session_id, None)

    def get(self, session_id: int) -> Session | None:
        with self._lock:
            return self._sessions.get(session_id)

    def all(self) -> list[Session]:
        with self._lock:
            return list(self._sessions.values())


class SessionHandler:
    """Concurrent metadata collector for cooperative lab clients.

    The wire protocol accepts one JSON hello object and then keeps the connection
    as a session. It deliberately exposes no remote command execution channel.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 8765, tls_context: ssl.SSLContext | None = None) -> None:
        self.host = host
        self.port = port
        self.tls_context = tls_context
        self.registry = SessionRegistry()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._server: asyncio.AbstractServer | None = None
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self.log = logging.getLogger(__name__)

    async def _client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        peer = writer.get_extra_info("peername") or ("unknown", 0)
        transport = "tls" if writer.get_extra_info("ssl_object") else "tcp"
        session: Session | None = None
        try:
            raw = await asyncio.wait_for(reader.readline(), timeout=10)
            hello = json.loads(raw.decode("utf-8")) if raw else {}
            hostname = str(hello.get("hostname", "unknown"))[:255]
            session = Session(0, str(peer[0]), int(peer[1]), hostname, datetime.now(timezone.utc), writer, transport)
            sid = self.registry.add(session)
            writer.write((json.dumps({"session_id": sid, "status": "registered"}) + "\n").encode())
            await writer.drain()
            while not self._stop.is_set():
                await asyncio.sleep(1)
        except (asyncio.TimeoutError, ConnectionError, OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            self.log.info("session connection ended: %s", exc)
        finally:
            if session is not None:
                self.registry.remove(session.session_id)
            writer.close()
            try:
                await writer.wait_closed()
            except OSError:
                pass

    async def _serve(self) -> None:
        self._server = await asyncio.start_server(self._client, self.host, self.port, ssl=self.tls_context)
        async with self._server:
            await self._server.serve_forever()

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="session-handler", daemon=True)
        self._thread.start()

    def _run(self) -> None:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._serve())
        except asyncio.CancelledError:
            pass
        except OSError as exc:
            self.log.error("session listener failed: %s", exc)
        finally:
            self._loop.close()
            self._loop = None

    def stop(self) -> None:
        self._stop.set()
        if self._loop and self._server:
            self._loop.call_soon_threadsafe(self._server.close)
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None

    def sessions(self) -> list[Session]:
        return self.registry.all()
