from __future__ import annotations

import asyncio
import json
import queue
import socket
import threading
import time
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest

from app.application.services.job_service import JobService
from app.config.settings import Settings
from app.domain.job import JobStatus
from app.infrastructure.repository.sqlite_repository import SQLiteJobRepository
from app.infrastructure.websocket.client import WebSocketClient
from app.infrastructure.websocket.command_handler import (
    CancelCommandHandler,
    PingCommandHandler,
    PrintCommandHandler,
)
from app.infrastructure.websocket.dispatcher import MessageDispatcher
from app.infrastructure.websocket.messages import ProtocolEnvelope, utc_now
from app.services.print_manager import PrinterManager
from app.services.print_service import PrintService


def test_e2e_websocket_print_ack_and_completed(tmp_path: Path) -> None:
    """Mock server print -> enqueue ACK -> PrintService -> completed (mock printer)."""
    websockets = pytest.importorskip("websockets")

    host = "127.0.0.1"
    with socket.socket() as sock:
        sock.bind((host, 0))
        port = sock.getsockname()[1]

    token = "demo-token"
    company_id = "test-company"
    server_ready = threading.Event()
    stop_server = threading.Event()

    async def mock_handler(websocket: Any) -> None:
        try:
            async for raw in websocket:
                data = json.loads(raw)
                if data.get("type") == "auth":
                    envelope = {
                        "version": "1.0",
                        "id": str(uuid4()),
                        "timestamp": utc_now(),
                        "type": "print",
                        "computer_id": str(data.get("computer_id", "server")),
                        "company_id": company_id,
                        "token": token,
                        "payload": {
                            "external_job_id": "crm-e2e-1",
                            "printer_name": "Mock Argox",
                            "template": "default",
                            "copies": 1,
                            "content": {
                                "company": "E2E",
                                "product": "Test",
                                "codigo": "E2E-001",
                                "preco": "1,00",
                            },
                        },
                    }
                    await websocket.send(json.dumps(envelope))
                if stop_server.is_set():
                    break
        except Exception:  # noqa: BLE001
            return

    async def run_server() -> None:
        async with websockets.serve(mock_handler, host, port):
            server_ready.set()
            while not stop_server.is_set():
                await asyncio.sleep(0.05)

    threading.Thread(target=lambda: asyncio.run(run_server()), daemon=True).start()
    assert server_ready.wait(5), "mock server did not start"

    settings = Settings()
    settings.base_dir = tmp_path
    settings.server_url = f"ws://{host}:{port}"
    settings.token = token
    settings.company_id = company_id
    settings.computer_id = str(uuid4())
    settings.mock_mode = True
    settings.auto_reconnect = False
    settings.default_printer = "Mock Argox"
    settings.printer_type = "Argox"
    settings.command_language = "PPLB"
    settings.connect_timeout_seconds = 3
    settings.read_timeout_seconds = 1
    settings.heartbeat_interval_seconds = 120

    repo = SQLiteJobRepository(tmp_path / "jobs.sqlite3")
    job_service = JobService(repo)
    manager = PrinterManager(base_dir=tmp_path)
    outbound: list[ProtocolEnvelope] = []
    send_queue: queue.Queue[ProtocolEnvelope | None] = queue.Queue()

    def send_callback(envelope: ProtocolEnvelope) -> None:
        outbound.append(envelope)
        send_queue.put(envelope)

    dispatcher = MessageDispatcher()
    dispatcher.register(
        "print",
        PrintCommandHandler(_job_service=job_service, _settings=settings, _send_callback=send_callback),
    )
    dispatcher.register(
        "ping",
        PingCommandHandler(_settings=settings, _send_callback=send_callback),
    )
    dispatcher.register(
        "cancel",
        CancelCommandHandler(_job_service=job_service, _settings=settings, _send_callback=send_callback),
    )

    print_service = PrintService(
        job_service=job_service,
        printer_manager=manager,
        settings=settings,
        send_callback=send_callback,
    )
    client = WebSocketClient(settings, dispatcher, send_queue, stop_event=None)
    client.connect()

    deadline = time.time() + 10
    while time.time() < deadline:
        for job in job_service.get_pending_jobs():
            print_service.process_job(job)
        if any(e.type == "completed" for e in outbound):
            break
        time.sleep(0.1)

    client.stop()
    stop_server.set()

    types = [e.type for e in outbound]
    assert "ack" in types, f"expected ack in {types}"
    assert "completed" in types, f"expected completed in {types}"

    job = job_service.get_by_external_job_id("crm-e2e-1")
    assert job is not None
    assert job.status == JobStatus.PRINTED

    ops_log = tmp_path / "logs" / "printer_operations.log"
    assert ops_log.exists()
    assert "success" in ops_log.read_text(encoding="utf-8")
