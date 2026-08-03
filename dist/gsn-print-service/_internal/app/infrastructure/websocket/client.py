from __future__ import annotations

import json
import threading
import time
from typing import Any

import websocket
from loguru import logger

from app.application.services.job_service import JobService
from app.config.settings import Settings
from app.domain.job import JobStatus, PrintJob
from app.services.print_service import PrintService


class WebSocketClient:
    def __init__(self, settings: Settings, job_service: JobService, print_service: PrintService) -> None:
        self._settings = settings
        self._job_service = job_service
        self._print_service = print_service
        self._ws: websocket.WebSocket | None = None
        self._running = False
        self._thread: threading.Thread | None = None

    def connect(self) -> None:
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def disconnect(self) -> None:
        self._running = False
        if self._ws:
            self._ws.close()

    def _run(self) -> None:
        while self._running:
            try:
                self._ws = websocket.create_connection(self._settings.server_url, timeout=5)
                logger.info("Connected to websocket")
                self._send_heartbeat_loop()
            except Exception as exc:  # noqa: BLE001
                logger.exception("Websocket failed: {exc}", exc=exc)
                time.sleep(5)

    def _send_heartbeat_loop(self) -> None:
        while self._running:
            try:
                if self._ws is None:
                    break
                payload = {"type": "heartbeat", "computer_name": self._settings.computer_name}
                self._ws.send(json.dumps(payload))
                time.sleep(self._settings.heartbeat_interval_seconds)
            except Exception as exc:  # noqa: BLE001
                logger.exception("Heartbeat failed: {exc}", exc=exc)
                break

    def on_message(self, message: str) -> None:
        data = json.loads(message)
        if data.get("type") != "print":
            return
        job = PrintJob(
            printer_name=data.get("printer", ""),
            template=data.get("template", "default"),
            payload=data.get("payload", {}),
            copies=int(data.get("copies", 1)),
        )
        self._job_service.enqueue(job)
        self._print_service.process_job(job)
