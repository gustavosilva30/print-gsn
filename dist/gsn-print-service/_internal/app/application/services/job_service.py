from __future__ import annotations

from app.domain.job import JobStatus, PrintJob
from app.infrastructure.repository.sqlite_repository import SQLiteJobRepository


class JobService:
    def __init__(self, repository: SQLiteJobRepository) -> None:
        self._repository = repository

    def enqueue(self, job: PrintJob) -> PrintJob:
        self._repository.save(job)
        return job

    def get_pending_jobs(self) -> list[PrintJob]:
        return self._repository.list_by_status(JobStatus.PENDING)

    def update_status(self, job_id: str, status: JobStatus, error: str | None = None) -> None:
        self._repository.update_status(job_id, status, error)
