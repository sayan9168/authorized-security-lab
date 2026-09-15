from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field
from threading import RLock
from typing import Any, Callable
from uuid import uuid4

from aslab.core.events import EventBus


@dataclass
class Job:
    job_id: str
    name: str
    status: str = "queued"
    result: Any = None
    error: str | None = None


class AssessmentJobManager:
    def __init__(self, workers: int = 4, events: EventBus | None = None) -> None:
        self._executor = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="assessment")
        self._events = events or EventBus()
        self._jobs: dict[str, Job] = {}
        self._lock = RLock()

    def submit(self, name: str, task: Callable[[], Any]) -> str:
        job_id = str(uuid4())
        job = Job(job_id, name)
        with self._lock:
            self._jobs[job_id] = job
        self._events.publish("job.queued", job_id=job_id, name=name)
        self._executor.submit(self._execute, job_id, task)
        return job_id

    def _execute(self, job_id: str, task: Callable[[], Any]) -> None:
        with self._lock:
            job = self._jobs[job_id]
            job.status = "running"
        self._events.publish("job.started", job_id=job_id)
        try:
            result = task()
            with self._lock:
                job.result, job.status = result, "completed"
            self._events.publish("job.completed", job_id=job_id)
        except Exception as exc:
            with self._lock:
                job.error, job.status = str(exc), "failed"
            self._events.publish("job.failed", job_id=job_id, error=str(exc))

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)

    def list(self) -> list[Job]:
        with self._lock:
            return list(self._jobs.values())

    def shutdown(self) -> None:
        self._executor.shutdown(wait=True, cancel_futures=True)
