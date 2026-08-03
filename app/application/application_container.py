from __future__ import annotations

import queue
from types import SimpleNamespace

from app.application.service_registry import ServiceRegistry
from app.application.services.job_service import JobService
from app.config.settings import Settings
from app.core.logging import configure_logging
from app.infrastructure.repository.sqlite_repository import SQLiteJobRepository
from app.infrastructure.websocket.client import WebSocketClient
from app.infrastructure.websocket.command_handler import (
    CancelCommandHandler,
    ConfigCommandHandler,
    PingCommandHandler,
    PrintCommandHandler,
    RestartCommandHandler,
    UpdateCommandHandler,
)
from app.infrastructure.websocket.dispatcher import MessageDispatcher
from app.infrastructure.websocket.messages import ProtocolEnvelope
from app.services.print_manager import PrinterManager
from app.services.print_service import PrintService


class ApplicationContainer:
    def __init__(self, settings: Settings, stop_event: object | None = None) -> None:
        self._settings = settings
        self._stop_event = stop_event
        self._registry = ServiceRegistry()
        self._services: SimpleNamespace | None = None

    def build(self) -> SimpleNamespace:
        configure_logging(self._settings.base_dir)

        # ------------------------------------------------------------------
        # Singletons (shared state across the process)
        # ------------------------------------------------------------------
        repository = SQLiteJobRepository(self._settings.base_dir / "database" / "jobs.sqlite3")
        self._registry.register_instance(Settings, self._settings)
        self._registry.register_instance(SQLiteJobRepository, repository)

        job_service = JobService(repository)
        self._registry.register_instance(JobService, job_service)

        printer_manager = PrinterManager()
        self._registry.register_instance(PrinterManager, printer_manager)

        print_service = PrintService(job_service, stop_event=self._stop_event)
        self._registry.register_instance(PrintService, print_service)

        # ------------------------------------------------------------------
        # WebSocket plumbing
        # ------------------------------------------------------------------
        send_queue: queue.Queue[ProtocolEnvelope | None] = queue.Queue()

        dispatcher = MessageDispatcher()

        # Lazy send callback — resolved after WebSocketClient is created
        _send_ref: list[WebSocketClient | None] = [None]

        def _send_callback(envelope: ProtocolEnvelope) -> None:
            client = _send_ref[0]
            if client is not None:
                client.send_envelope(envelope)

        dispatcher.register(
            "print",
            PrintCommandHandler(
                _job_service=job_service,
                _settings=self._settings,
                _send_callback=_send_callback,
            ),
        )
        dispatcher.register(
            "cancel",
            CancelCommandHandler(
                _job_service=job_service,
                _settings=self._settings,
                _send_callback=_send_callback,
            ),
        )
        dispatcher.register(
            "ping",
            PingCommandHandler(
                _settings=self._settings,
                _send_callback=_send_callback,
            ),
        )
        dispatcher.register(
            "config",
            ConfigCommandHandler(
                _settings=self._settings,
                _send_callback=_send_callback,
            ),
        )
        dispatcher.register(
            "update",
            UpdateCommandHandler(
                _send_callback=_send_callback,
                _settings=self._settings,
            ),
        )
        dispatcher.register(
            "restart",
            RestartCommandHandler(
                _send_callback=_send_callback,
                _settings=self._settings,
            ),
        )

        websocket_client = WebSocketClient(
            settings=self._settings,
            dispatcher=dispatcher,
            send_queue=send_queue,
            stop_event=self._stop_event,
        )
        _send_ref[0] = websocket_client
        self._registry.register_instance(WebSocketClient, websocket_client)

        print_service.start()
        websocket_client.connect()

        self._services = SimpleNamespace(
            print_service=print_service,
            websocket_client=websocket_client,
            printer_manager=printer_manager,
        )
        return self._services
