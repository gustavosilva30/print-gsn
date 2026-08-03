from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.domain.job import JobStatus


class ProtocolMessageError(ValueError):
    """Raised when a protocol envelope is invalid."""


@dataclass(slots=True)
class ProtocolEnvelope:
    version: str
    id: str
    timestamp: str
    type: str
    computer_id: str
    company_id: str
    token: str
    payload: dict[str, Any]

    @classmethod
    def from_json(cls, raw_message: str) -> "ProtocolEnvelope":
        try:
            data = json.loads(raw_message)
        except json.JSONDecodeError as exc:
            raise ProtocolMessageError("Invalid JSON message") from exc
        if not isinstance(data, dict):
            raise ProtocolMessageError("Protocol envelope must be a JSON object")
        required_fields = {
            "version",
            "id",
            "timestamp",
            "type",
            "computer_id",
            "company_id",
            "token",
            "payload",
        }
        missing_fields = sorted(required_fields.difference(data.keys()))
        if missing_fields:
            raise ProtocolMessageError(f"Missing required fields: {', '.join(missing_fields)}")
        payload = data["payload"]
        if not isinstance(payload, dict):
            raise ProtocolMessageError("Protocol payload must be an object")
        return cls(
            version=str(data["version"]),
            id=str(data["id"]),
            timestamp=str(data["timestamp"]),
            type=str(data["type"]),
            computer_id=str(data["computer_id"]),
            company_id=str(data["company_id"]),
            token=str(data["token"]),
            payload=payload,
        )

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=True)


def build_envelope(
    message_type: str,
    *,
    version: str,
    computer_id: str,
    company_id: str,
    token: str,
    payload: dict[str, Any],
    message_id: str | None = None,
    timestamp: str | None = None,
) -> ProtocolEnvelope:
    return ProtocolEnvelope(
        version=version,
        id=message_id or str(uuid4()),
        timestamp=timestamp or utc_now(),
        type=message_type,
        computer_id=computer_id,
        company_id=company_id,
        token=token,
        payload=payload,
    )


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def job_status_to_protocol_status(status: JobStatus) -> str:
    mapping = {
        JobStatus.PENDING: "queued",
        JobStatus.DOWNLOADING: "processing",
        JobStatus.PROCESSING: "processing",
        JobStatus.PRINTING: "printing",
        JobStatus.PRINTED: "printed",
        JobStatus.FAILED: "failed",
        JobStatus.CANCELED: "canceled",
    }
    return mapping.get(status, status.value.lower())
