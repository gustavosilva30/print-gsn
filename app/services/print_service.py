from __future__ import annotations

import threading
import time
from typing import Any

from loguru import logger

from app.application.services.job_service import JobService
from app.domain.job import JobStatus, PrintJob


class PrintService:
    def __init__(self, job_service: JobService, stop_event: Any | None = None) -> None:
        self._job_service = job_service
        self._running = False
        self._thread: threading.Thread | None = None
        self._stop_event = stop_event

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=False)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._stop_event is not None:
            self._stop_event.set()

    def process_job(self, job: PrintJob) -> None:
        self._job_service.update_status(job.id, JobStatus.PRINTING)
        logger.info("Printing job {job_id}", job_id=job.id)
        time.sleep(0.2)
        self._job_service.update_status(job.id, JobStatus.PRINTED)

    def _loop(self) -> None:
        while self._running:
            if self._stop_event is not None and self._stop_event.is_set():
                break
            for job in self._job_service.get_pending_jobs():
                self.process_job(job)
            if self._stop_event is not None:
                self._stop_event.wait(1)
            else:
                time.sleep(1)
