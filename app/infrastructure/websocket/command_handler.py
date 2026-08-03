from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Protocol

from loguru import logger

from app.application.services.job_service import JobService
from app.config.settings import Settings
from app.domain.job import JobStatus, PrintJob
from app.infrastructure.websocket.messages import (
    ProtocolEnvelope,
    build_envelope,
    job_status_to_protocol_status,
    utc_now,
)


class CommandHandler(Protocol):
    def __call__(self, envelope: ProtocolEnvelope) -> ProtocolEnvelope | None: ...


@dataclass(slots=True)
class PrintCommandHandler:
    _job_service: JobService
    _settings: Settings
    _send_callback: Callable[[ProtocolEnvelope], None]

    def __call__(self, envelope: ProtocolEnvelope) -> ProtocolEnvelope | None:
        payload = envelope.payload
        if envelope.id:
            existing = self._job_service.get_by_remote_message_id(envelope.id)
            if existing is not None:
                logger.info("Duplicate remote message {remote_id}, existing job {job_id}", remote_id=envelope.id, job_id=existing.id)
                return None
        printer_name = str(
            payload.get("printer_name")
            or payload.get("printer")
            or self._settings.default_printer
            or ""
        )
        template = str(payload.get("template", "default"))
        data = payload.get("content") or payload.get("data") or payload.get("payload")
        if not isinstance(data, dict):
            data = {}
        copies = max(1, int(payload.get("copies", self._settings.copies or 1)))
        external_job_id = str(payload.get("external_job_id", "")) or None
        job = PrintJob(
            printer_name=printer_name,
            template=template,
            payload=data,
            copies=copies,
            remote_message_id=envelope.id or None,
            external_job_id=external_job_id,
            company_id=envelope.company_id or self._settings.company_id,
            metadata={
                "source": "websocket",
                "received_at": utc_now(),
                "server_message_id": envelope.id,
                "server_timestamp": envelope.timestamp,
            },
        )
        self._job_service.enqueue(job)
        logger.info(
            "Job enqueued {job_id} | printer={printer} | template={template} | copies={copies}",
            job_id=job.id,
            printer=printer_name,
            template=template,
            copies=copies,
        )
        ack = build_envelope(
            message_type="ack",
            version=self._settings.protocol_version,
            computer_id=self._settings.computer_id,
            company_id=self._settings.company_id,
            token=self._settings.token,
            payload={
                "message_id": envelope.id,
                "job_id": job.id,
                "external_job_id": external_job_id,
                "status": "queued",
                "queued_at": utc_now(),
            },
        )
        self._send_callback(ack)
        return None


@dataclass(slots=True)
class CancelCommandHandler:
    _job_service: JobService
    _settings: Settings
    _send_callback: Callable[[ProtocolEnvelope], None]

    def __call__(self, envelope: ProtocolEnvelope) -> ProtocolEnvelope | None:
        payload = envelope.payload
        job_id = str(payload.get("job_id", "")) or None
        external_job_id = str(payload.get("external_job_id", "")) or None
        job = None
        if job_id:
            job = self._job_service.get_by_id(job_id)
        if job is None and external_job_id:
            job = self._job_service.get_by_external_job_id(external_job_id)
        if job is None:
            logger.warning("Cancel requested for unknown job | job_id={job_id} | external_job_id={ext_id}", job_id=job_id, ext_id=external_job_id)
            return None
        if job.status in (JobStatus.CANCELED, JobStatus.PRINTED, JobStatus.FAILED):
            logger.info("Cancel skipped for job {job_id} (status={status})", job_id=job.id, status=job.status.value)
            return None
        self._job_service.cancel(job_id=job.id)
        ack = build_envelope(
            message_type="ack",
            version=self._settings.protocol_version,
            computer_id=self._settings.computer_id,
            company_id=self._settings.company_id,
            token=self._settings.token,
            payload={
                "message_id": envelope.id,
                "job_id": job.id,
                "external_job_id": external_job_id,
                "status": "canceled",
                "canceled_at": utc_now(),
            },
        )
        self._send_callback(ack)
        return None


@dataclass(slots=True)
class PingCommandHandler:
    _settings: Settings
    _send_callback: Callable[[ProtocolEnvelope], None]

    def __call__(self, envelope: ProtocolEnvelope) -> ProtocolEnvelope | None:
        pong = build_envelope(
            message_type="pong",
            version=self._settings.protocol_version,
            computer_id=self._settings.computer_id,
            company_id=self._settings.company_id,
            token=self._settings.token,
            payload={
                "request_id": envelope.id,
                "server_timestamp": envelope.timestamp,
                "pong_at": utc_now(),
            },
        )
        self._send_callback(pong)
        return None


@dataclass(slots=True)
class ConfigCommandHandler:
    _settings: Settings
    _send_callback: Callable[[ProtocolEnvelope], None]

    def __call__(self, envelope: ProtocolEnvelope) -> ProtocolEnvelope | None:
        config_response = build_envelope(
            message_type="status",
            version=self._settings.protocol_version,
            computer_id=self._settings.computer_id,
            company_id=self._settings.company_id,
            token=self._settings.token,
            payload={
                "request_id": envelope.id,
                "status": "online",
                "config": {
                    "default_printer": self._settings.default_printer,
                    "printer_type": self._settings.printer_type,
                    "label_language": self._settings.label_language,
                    "copies": self._settings.copies,
                    "paper_width": self._settings.paper_width,
                    "paper_height": self._settings.paper_height,
                    "service_version": self._settings.service_version,
                },
            },
        )
        self._send_callback(config_response)
        return None


@dataclass(slots=True)
class UpdateCommandHandler:
    _send_callback: Callable[[ProtocolEnvelope], None]
    _settings: Settings

    def __call__(self, envelope: ProtocolEnvelope) -> ProtocolEnvelope | None:
        version = str(envelope.payload.get("version", ""))
        logger.info("Update command received | version={version}", version=version)
        ack = build_envelope(
            message_type="ack",
            version=self._settings.protocol_version,
            computer_id=self._settings.computer_id,
            company_id=self._settings.company_id,
            token=self._settings.token,
            payload={
                "message_id": envelope.id,
                "command": "update",
                "status": "acknowledged",
                "current_version": self._settings.service_version,
                "requested_version": version,
            },
        )
        self._send_callback(ack)
        return None


@dataclass(slots=True)
class RestartCommandHandler:
    _send_callback: Callable[[ProtocolEnvelope], None]
    _settings: Settings

    def __call__(self, envelope: ProtocolEnvelope) -> ProtocolEnvelope | None:
        logger.info("Restart command received")
        ack = build_envelope(
            message_type="ack",
            version=self._settings.protocol_version,
            computer_id=self._settings.computer_id,
            company_id=self._settings.company_id,
            token=self._settings.token,
            payload={
                "message_id": envelope.id,
                "command": "restart",
                "status": "acknowledged",
            },
        )
        self._send_callback(ack)
        return None
