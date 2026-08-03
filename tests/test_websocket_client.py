from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.config.settings import Settings
from app.infrastructure.websocket.client import WebSocketClient
from app.infrastructure.websocket.dispatcher import MessageDispatcher
from app.infrastructure.websocket.messages import ProtocolEnvelope, build_envelope
import queue


def test_client_connect_and_stop() -> None:
    settings = Settings()
    settings.server_url = "ws://127.0.0.1:1"
    settings.auto_reconnect = False
    dispatcher = MessageDispatcher()
    send_queue: queue.Queue[ProtocolEnvelope | None] = queue.Queue()
    client = WebSocketClient(settings, dispatcher, send_queue)

    client.connect()
    assert client._running
    client.stop()
    assert not client._running


def test_client_send_envelope_queues_message() -> None:
    settings = Settings()
    settings.server_url = "ws://127.0.0.1:1"
    settings.auto_reconnect = False
    dispatcher = MessageDispatcher()
    send_queue: queue.Queue[ProtocolEnvelope | None] = queue.Queue()
    client = WebSocketClient(settings, dispatcher, send_queue)

    envelope = build_envelope(
        message_type="heartbeat",
        version=settings.protocol_version,
        computer_id=settings.computer_id,
        company_id=settings.company_id,
        token=settings.token,
        payload={"test": True},
    )
    client.send_envelope(envelope)
    assert send_queue.qsize() == 1


def test_client_disconnect_clears_ws() -> None:
    settings = Settings()
    settings.server_url = "ws://127.0.0.1:1"
    settings.auto_reconnect = False
    dispatcher = MessageDispatcher()
    send_queue: queue.Queue[ProtocolEnvelope | None] = queue.Queue()
    client = WebSocketClient(settings, dispatcher, send_queue)

    client.disconnect()
    assert not client._running


def test_client_rejects_http_url() -> None:
    settings = Settings()
    settings.server_url = "http://example.com"
    settings.auto_reconnect = False
    dispatcher = MessageDispatcher()
    send_queue: queue.Queue[ProtocolEnvelope | None] = queue.Queue()
    client = WebSocketClient(settings, dispatcher, send_queue)

    assert not client._is_supported_url()
