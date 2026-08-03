from __future__ import annotations

import json

import pytest

from app.infrastructure.websocket.messages import (
    ProtocolEnvelope,
    ProtocolMessageError,
    build_envelope,
    job_status_to_protocol_status,
    utc_now,
)
from app.domain.job import JobStatus


def test_envelope_from_valid_json() -> None:
    raw = json.dumps({
        "version": "1.0",
        "id": "msg-1",
        "timestamp": "2026-01-01T00:00:00Z",
        "type": "print",
        "computer_id": "comp-1",
        "company_id": "co-1",
        "token": "tok",
        "payload": {"printer": "Argox", "data": {"code": "X"}},
    })
    envelope = ProtocolEnvelope.from_json(raw)
    assert envelope.version == "1.0"
    assert envelope.id == "msg-1"
    assert envelope.type == "print"
    assert envelope.payload == {"printer": "Argox", "data": {"code": "X"}}


def test_envelope_from_invalid_json_raises() -> None:
    with pytest.raises(ProtocolMessageError, match="Invalid JSON"):
        ProtocolEnvelope.from_json("not json")


def test_envelope_missing_field_raises() -> None:
    raw = json.dumps({"version": "1.0", "id": "msg-1"})
    with pytest.raises(ProtocolMessageError, match="Missing required fields"):
        ProtocolEnvelope.from_json(raw)


def test_envelope_payload_not_object_raises() -> None:
    raw = json.dumps({
        "version": "1.0",
        "id": "msg-1",
        "timestamp": "2026-01-01T00:00:00Z",
        "type": "print",
        "computer_id": "comp-1",
        "company_id": "co-1",
        "token": "tok",
        "payload": "not an object",
    })
    with pytest.raises(ProtocolMessageError, match="payload must be an object"):
        ProtocolEnvelope.from_json(raw)


def test_envelope_roundtrip() -> None:
    envelope = build_envelope(
        message_type="ack",
        version="1.0",
        computer_id="c1",
        company_id="co1",
        token="tok",
        payload={"job_id": "j1", "status": "queued"},
        message_id="ack-1",
        timestamp="2026-01-01T00:00:00Z",
    )
    json_str = envelope.to_json()
    parsed = ProtocolEnvelope.from_json(json_str)
    assert parsed.id == "ack-1"
    assert parsed.type == "ack"
    assert parsed.payload["job_id"] == "j1"


def test_build_envelope_auto_id_and_timestamp() -> None:
    envelope = build_envelope(
        message_type="heartbeat",
        version="1.0",
        computer_id="c1",
        company_id="co1",
        token="tok",
        payload={},
    )
    assert len(envelope.id) > 0
    assert envelope.timestamp.endswith("Z")


def test_job_status_mapping() -> None:
    assert job_status_to_protocol_status(JobStatus.PENDING) == "queued"
    assert job_status_to_protocol_status(JobStatus.PRINTED) == "printed"
    assert job_status_to_protocol_status(JobStatus.FAILED) == "failed"
    assert job_status_to_protocol_status(JobStatus.CANCELED) == "canceled"
