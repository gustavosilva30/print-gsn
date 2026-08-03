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

    def count_pending_jobs(self) -> int:
        return len(self.get_pending_jobs())

    def get_by_id(self, job_id: str) -> PrintJob | None:
        return self._repository.get_by_id(job_id)

    def get_by_remote_message_id(self, remote_message_id: str) -> PrintJob | None:
        return self._repository.get_by_remote_message_id(remote_message_id)

    def get_by_external_job_id(self, external_job_id: str) -> PrintJob | None:
        return self._repository.get_by_external_job_id(external_job_id)

    def cancel(self, job_id: str | None = None, external_job_id: str | None = None) -> PrintJob | None:
        job = None
        if job_id:
            job = self.get_by_id(job_id)
        elif external_job_id:
            job = self.get_by_external_job_id(external_job_id)
        if job is None:
            return None
        self.update_status(job.id, JobStatus.CANCELED)
        job.status = JobStatus.CANCELED
        return job

    def update_status(self, job_id: str, status: JobStatus, error: str | None = None) -> None:
        self._repository.update_status(job_id, status, error)
