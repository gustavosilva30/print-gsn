from __future__ import annotations

import threading
import time
from typing import Any, Callable

from loguru import logger

from app.application.services.job_service import JobService
from app.config.settings import Settings
from app.domain.job import JobStatus, PrintJob
from app.infrastructure.websocket.messages import ProtocolEnvelope, build_envelope, utc_now
from app.services.print_manager import PrinterManager


class PrintService:
    """Worker that drains the local job queue and prints via PrinterManager."""

    def __init__(
        self,
        job_service: JobService,
        printer_manager: PrinterManager | None = None,
        settings: Settings | None = None,
        stop_event: Any | None = None,
        send_callback: Callable[[ProtocolEnvelope], None] | None = None,
    ) -> None:
        self._job_service = job_service
        self._printer_manager = printer_manager or PrinterManager()
        self._settings = settings or Settings()
        self._stop_event = stop_event
        self._send_callback = send_callback
        self._running = False
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=False, name="print-service")
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._stop_event is not None:
            self._stop_event.set()

    def process_job(self, job: PrintJob) -> None:
        """Process a single job: print via PrinterManager and notify the server."""
        if job.status == JobStatus.CANCELED:
            logger.info("Skipping canceled job {job_id}", job_id=job.id)
            return

        self._job_service.update_status(job.id, JobStatus.PRINTING)
        logger.info(
            "Printing job {job_id} | printer={printer} | template={template} | copies={copies}",
            job_id=job.id,
            printer=job.printer_name or self._settings.default_printer,
            template=job.template,
            copies=job.copies,
        )

        try:
            self._printer_manager.print_job(
                job,
                mock=self._settings.mock_mode,
                default_printer=self._settings.default_printer,
                printer_type=self._settings.printer_type,
                paper_width=self._settings.paper_width,
                paper_height=self._settings.paper_height,
                label_language=self._settings.label_language,
                command_language=getattr(self._settings, "command_language", "PPLB"),
                argox_model=getattr(self._settings, "argox_model", "OS-214 Plus"),
                argox_dpi=getattr(self._settings, "argox_dpi", 203),
                argox_darkness=getattr(self._settings, "argox_darkness", 10),
                argox_speed=getattr(self._settings, "argox_speed", 3),
            )
            self._job_service.update_status(job.id, JobStatus.PRINTED)
            logger.info("Job printed successfully {job_id}", job_id=job.id)
            self._notify_completed(job)
        except Exception as exc:  # noqa: BLE001
            error_message = str(exc) or "Unknown print error"
            logger.exception("Job failed {job_id}: {error}", job_id=job.id, error=error_message)
            self._job_service.update_status(job.id, JobStatus.FAILED, error=error_message)
            self._notify_failed(job, reason=error_message, code="PRINT_ERROR")

    def _notify_completed(self, job: PrintJob) -> None:
        if self._send_callback is None:
            return
        envelope = build_envelope(
            message_type="completed",
            version=self._settings.protocol_version,
            computer_id=self._settings.computer_id,
            company_id=self._settings.company_id,
            token=self._settings.token,
            payload={
                "job_id": job.id,
                "external_job_id": job.external_job_id,
                "message_id": job.remote_message_id,
                "printed_at": utc_now(),
                "status": "printed",
            },
        )
        try:
            self._send_callback(envelope)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to send completed notification for {job_id}: {exc}", job_id=job.id, exc=exc)

    def _notify_failed(self, job: PrintJob, *, reason: str, code: str) -> None:
        if self._send_callback is None:
            return
        envelope = build_envelope(
            message_type="failed",
            version=self._settings.protocol_version,
            computer_id=self._settings.computer_id,
            company_id=self._settings.company_id,
            token=self._settings.token,
            payload={
                "job_id": job.id,
                "external_job_id": job.external_job_id,
                "message_id": job.remote_message_id,
                "reason": reason,
                "code": code,
                "status": "failed",
                "failed_at": utc_now(),
            },
        )
        try:
            self._send_callback(envelope)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to send failed notification for {job_id}: {exc}", job_id=job.id, exc=exc)

    def _loop(self) -> None:
        while self._running:
            if self._stop_event is not None and self._stop_event.is_set():
                break
            for job in self._job_service.get_pending_jobs():
                if not self._running:
                    break
                current = self._job_service.get_by_id(job.id)
                if current is None or current.status != JobStatus.PENDING:
                    continue
                self.process_job(current)
            if self._stop_event is not None:
                self._stop_event.wait(1)
            else:
                time.sleep(1)
