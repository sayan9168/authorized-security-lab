from __future__ import annotations

import threading
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, Any


class JobState(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(slots=True)
class ScheduledJob:
    job_id: str
    name: str
    state: JobState = JobState.QUEUED
    created_at: str = ""
    started_at: str = ""
    finished_at: str = ""
    error: str = ""


class JobScheduler:
    """Small bounded scheduler for safe assessment jobs."""

    def __init__(self, workers: int = 4) -> None:
        if workers < 1 or workers > 32:
            raise ValueError("workers must be between 1 and 32")
        self._executor = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="aslab-job")
        self._jobs: dict[str, ScheduledJob] = {}
        self._futures: dict[str, Future[Any]] = {}
        self._lock = threading.RLock()

    def submit(self, job_id: str, name: str, fn: Callable[[], Any]) -> ScheduledJob:
        with self._lock:
            if job_id in self._jobs:
                raise ValueError(f"job already exists: {job_id}")
            job = ScheduledJob(job_id, name, created_at=datetime.now(timezone.utc).isoformat())
            self._jobs[job_id] = job
            future = self._executor.submit(self._execute, job_id, fn)
            self._futures[job_id] = future
            return job

    def _execute(self, job_id: str, fn: Callable[[], Any]) -> Any:
        with self._lock:
            job = self._jobs[job_id]
            job.state = JobState.RUNNING
            job.started_at = datetime.now(timezone.utc).isoformat()
        try:
            result = fn()
            with self._lock:
                job.state = JobState.COMPLETED
                job.finished_at = datetime.now(timezone.utc).isoformat()
            return result
        except Exception as exc:
            with self._lock:
                job.state = JobState.FAILED
                job.error = str(exc)
                job.finished_at = datetime.now(timezone.utc).isoformat()
            raise

    def get(self, job_id: str) -> ScheduledJob | None:
        with self._lock:
            return self._jobs.get(job_id)

    def all(self) -> list[ScheduledJob]:
        with self._lock:
            return list(self._jobs.values())

    def cancel(self, job_id: str) -> bool:
        with self._lock:
            future = self._futures.get(job_id)
            job = self._jobs.get(job_id)
            if future is None or job is None:
                return False
            cancelled = future.cancel()
            if cancelled:
                job.state = JobState.CANCELLED
                job.finished_at = datetime.now(timezone.utc).isoformat()
            return cancelled

    def shutdown(self) -> None:
        self._executor.shutdown(wait=True, cancel_futures=True)
