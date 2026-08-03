from __future__ import annotations

import signal
import threading
import time
from typing import Any

from loguru import logger

from app.application.application_container import ApplicationContainer
from app.application.lifecycle import LifecycleManager
from app.config.settings import Settings


class Application:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or Settings()
        self._stop_event = threading.Event()
        self._services: Any | None = None
        self._thread: threading.Thread | None = None
        self._lifecycle_manager: LifecycleManager | None = None

    def run(self) -> int:
        self._register_signal_handlers()
        logger.info("Starting GSN Print Service")
        container = ApplicationContainer(self._settings, stop_event=self._stop_event)
        self._services = container.build()
        self._lifecycle_manager = LifecycleManager(self._stop_event)
        if self._services is not None:
            self._lifecycle_manager.register(self._services.print_service)
            self._lifecycle_manager.register(self._services.websocket_client)
        self._thread = threading.Thread(target=self._wait_for_shutdown, daemon=False)
        self._thread.start()
        self._thread.join()
        self.shutdown()
        return 0

    def stop(self) -> None:
        logger.info("Stop requested")
        self._stop_event.set()
        if self._services is not None:
            for service_name in ("print_service", "websocket_client"):
                service = getattr(self._services, service_name, None)
                if service is not None and hasattr(service, "stop"):
                    service.stop()

    def shutdown(self) -> None:
        logger.info("Shutting down GSN Print Service")
        self.stop()

    def _register_signal_handlers(self) -> None:
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    def _handle_signal(self, signum: int, _frame: Any) -> None:
        logger.info("Received signal {signum}", signum=signum)
        self.stop()

    def _wait_for_shutdown(self) -> None:
        while not self._stop_event.wait(0.5):
            time.sleep(0.1)
