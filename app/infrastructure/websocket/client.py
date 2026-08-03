from __future__ import annotations

import json
import queue
import socket
import threading
import time
from typing import Any

import websocket
from loguru import logger

from app.config.settings import Settings
from app.infrastructure.websocket.backoff import ExponentialBackoff
from app.infrastructure.websocket.command_handler import (
    CancelCommandHandler,
    ConfigCommandHandler,
    PingCommandHandler,
    PrintCommandHandler,
    RestartCommandHandler,
    UpdateCommandHandler,
)
from app.infrastructure.websocket.dispatcher import MessageDispatcher
from app.infrastructure.websocket.messages import (
    ProtocolEnvelope,
    ProtocolMessageError,
    build_envelope,
    utc_now,
)


class WebSocketClient:
    def __init__(self, settings: Settings, dispatcher: MessageDispatcher, send_queue: queue.Queue[ProtocolEnvelope | None], stop_event: Any | None = None) -> None:
        self._settings = settings
        self._dispatcher = dispatcher
        self._send_queue = send_queue
        self._ws: websocket.WebSocket | None = None
        self._ws_lock = threading.Lock()
        self._running = False
        self._thread: threading.Thread | None = None
        self._stop_event = stop_event
        self._backoff = ExponentialBackoff(
            initial_delay_seconds=self._settings.reconnect_initial_delay_seconds,
            max_delay_seconds=self._settings.reconnect_max_delay_seconds,
            multiplier=self._settings.reconnect_multiplier,
        )

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def connect(self) -> None:
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=False, name="ws-client")
        self._thread.start()
        logger.info("WebSocket client started")

    def disconnect(self) -> None:
        self._running = False
        with self._ws_lock:
            ws = self._ws
            self._ws = None
        if ws is not None:
            try:
                ws.close()
            except Exception:  # noqa: BLE001
                pass
        self._send_queue.put(None)

    def stop(self) -> None:
        self._running = False
        if self._stop_event is not None:
            self._stop_event.set()
        self.disconnect()

    def send_envelope(self, envelope: ProtocolEnvelope) -> None:
        if self._settings.max_pending_outbound_messages > 0 and self._send_queue.qsize() >= self._settings.max_pending_outbound_messages:
            try:
                self._send_queue.get_nowait()
            except queue.Empty:
                pass
        self._send_queue.put(envelope)

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def _run(self) -> None:
        while self._running:
            if self._stop_event is not None and self._stop_event.is_set():
                break
            if not self._is_supported_url():
                logger.warning("WebSocket server URL not supported: {url}", url=self._settings.server_url)
                break
            try:
                self._connect_and_serve()
            except Exception as exc:  # noqa: BLE001
                logger.exception("WebSocket connection error: {exc}", exc=exc)
            if not self._running or (self._stop_event is not None and self._stop_event.is_set()):
                break
            if not self._settings.auto_reconnect:
                logger.info("Auto-reconnect disabled, stopping WebSocket client")
                break
            delay = self._backoff.next_delay()
            logger.info("Reconnecting in {delay:.1f}s", delay=delay)
            if self._sleep_interruptible(delay):
                break

    def _connect_and_serve(self) -> None:
        ws = websocket.create_connection(
            self._settings.server_url,
            timeout=self._settings.connect_timeout_seconds,
        )
        ws.settimeout(self._settings.read_timeout_seconds)
        self._backoff.reset()
        with self._ws_lock:
            self._ws = ws
        logger.info("WebSocket connected to {url}", url=self._settings.server_url)
        self._send_auth()
        sender_thread = threading.Thread(target=self._sender_loop, args=(ws,), daemon=True, name="ws-sender")
        sender_thread.start()
        heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True, name="ws-heartbeat")
        heartbeat_thread.start()
        self._receive_loop(ws)
        self._send_queue.put(None)
        with self._ws_lock:
            self._ws = None

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------

    def _send_auth(self) -> None:
        auth = build_envelope(
            message_type="auth",
            version=self._settings.protocol_version,
            computer_id=self._settings.computer_id,
            company_id=self._settings.company_id,
            token=self._settings.token,
            payload={
                "computer_name": self._settings.computer_name,
                "service_version": self._settings.service_version,
            },
        )
        self.send_envelope(auth)

    # ------------------------------------------------------------------
    # Heartbeat
    # ------------------------------------------------------------------

    def _heartbeat_loop(self) -> None:
        while self._running and not self._is_stop_set():
            try:
                heartbeat = build_envelope(
                    message_type="heartbeat",
                    version=self._settings.protocol_version,
                    computer_id=self._settings.computer_id,
                    company_id=self._settings.company_id,
                    token=self._settings.token,
                    payload={
                        "computer_name": self._settings.computer_name,
                        "service_version": self._settings.service_version,
                        "pending_jobs": 0,
                    },
                )
                self.send_envelope(heartbeat)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Heartbeat build failed: {exc}", exc=exc)
            self._sleep_interruptible(self._settings.heartbeat_interval_seconds)

    # ------------------------------------------------------------------
    # Receive loop
    # ------------------------------------------------------------------

    def _receive_loop(self, ws: websocket.WebSocket) -> None:
        while self._running and not self._is_stop_set():
            try:
                message = ws.recv()
            except websocket.WebSocketTimeoutException:
                continue
            except (websocket.WebSocketConnectionClosedException, ConnectionError, OSError) as exc:
                logger.warning("WebSocket receive error: {exc}", exc=exc)
                break
            except Exception as exc:  # noqa: BLE001
                logger.exception("Unexpected receive error: {exc}", exc=exc)
                break
            if not message:
                continue
            try:
                envelope = ProtocolEnvelope.from_json(message)
            except ProtocolMessageError as exc:
                logger.warning("Protocol error: {exc}", exc=exc)
                continue
            self._dispatcher.dispatch(envelope)

    # ------------------------------------------------------------------
    # Sender loop (drains _send_queue onto the active websocket)
    # ------------------------------------------------------------------

    def _sender_loop(self, ws: websocket.WebSocket) -> None:
        while self._running and not self._is_stop_set():
            try:
                item = self._send_queue.get(timeout=1)
            except queue.Empty:
                continue
            if item is None:
                break
            if not self._running or self._is_stop_set():
                self._send_queue.put(item)
                break
            try:
                ws.send(item.to_json())
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed to send message: {exc}", exc=exc)
                self._send_queue.put(item)
                break

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _is_supported_url(self) -> bool:
        url = self._settings.server_url
        return url.startswith("ws://") or url.startswith("wss://")

    def _is_stop_set(self) -> bool:
        return self._stop_event is not None and self._stop_event.is_set()

    def _sleep_interruptible(self, seconds: float) -> bool:
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            if not self._running or self._is_stop_set():
                return True
            time.sleep(min(0.2, deadline - time.monotonic()))
        return False
