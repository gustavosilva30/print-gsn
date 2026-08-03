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
        self._started = False

    @property
    def settings(self) -> Settings:
        return self._settings

    @property
    def services(self) -> Any | None:
        return self._services

    def start(self) -> None:
        """Start core services without blocking the caller."""
        if self._started:
            return
        logger.info("Starting GSN Print Service")
        container = ApplicationContainer(self._settings, stop_event=self._stop_event)
        self._services = container.build()
        self._lifecycle_manager = LifecycleManager(self._stop_event)
        if self._services is not None:
            self._lifecycle_manager.register(self._services.print_service)
            self._lifecycle_manager.register(self._services.websocket_client)
        self._started = True

    def run(self) -> int:
        """Headless mode: start services and block until stop signal."""
        self._register_signal_handlers()
        self.start()
        self._thread = threading.Thread(target=self._wait_for_shutdown, daemon=False, name="app-wait")
        self._thread.start()
        self._thread.join()
        self.shutdown()
        return 0

    def run_with_tray(self) -> int:
        """Interactive mode: start services and keep process alive via system tray."""
        self._register_signal_handlers()
        self.start()
        from app.ui.tray.tray import SystemTray

        tray = SystemTray(application=self)
        try:
            tray.run()
        finally:
            self.shutdown()
        return 0

    def stop(self) -> None:
        logger.info("Stop requested")
        self._stop_event.set()
        if self._services is not None:
            for service_name in ("print_service", "websocket_client", "local_http"):
                service = getattr(self._services, service_name, None)
                if service is not None and hasattr(service, "stop"):
                    service.stop()

    def shutdown(self) -> None:
        logger.info("Shutting down GSN Print Service")
        self.stop()
        self._started = False

    def status(self) -> dict[str, Any]:
        """Snapshot used by tray and diagnostics."""
        pending = 0
        ws_running = False
        print_running = False
        if self._services is not None:
            job_service = getattr(self._services, "job_service", None)
            if job_service is not None and hasattr(job_service, "count_pending_jobs"):
                try:
                    pending = int(job_service.count_pending_jobs())
                except Exception:  # noqa: BLE001
                    pending = 0
            ws = getattr(self._services, "websocket_client", None)
            if ws is not None:
                ws_running = bool(getattr(ws, "_running", False))
            ps = getattr(self._services, "print_service", None)
            if ps is not None:
                print_running = bool(getattr(ps, "_running", False))
        return {
            "started": self._started,
            "stopping": self._stop_event.is_set(),
            "pending_jobs": pending,
            "websocket_running": ws_running,
            "print_service_running": print_running,
            "mock_mode": self._settings.mock_mode,
            "default_printer": self._settings.default_printer,
            "server_url": self._settings.server_url,
            "computer_name": self._settings.computer_name,
            "service_version": self._settings.service_version,
        }

    def request_print_test(self) -> bool:
        if self._services is None:
            return False
        manager = getattr(self._services, "printer_manager", None)
        if manager is None:
            return False
        try:
            return bool(
                manager.print_test(
                    printer_name=self._settings.default_printer or None,
                    mock=self._settings.mock_mode,
                )
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("Print test failed: {exc}", exc=exc)
            return False

    def _register_signal_handlers(self) -> None:
        try:
            signal.signal(signal.SIGINT, self._handle_signal)
            signal.signal(signal.SIGTERM, self._handle_signal)
        except Exception:  # noqa: BLE001
            # Some environments (e.g. non-main threads / Windows service) disallow this
            logger.debug("Signal handlers not registered in this context")

    def _handle_signal(self, signum: int, _frame: Any) -> None:
        logger.info("Received signal {signum}", signum=signum)
        self.stop()

    def _wait_for_shutdown(self) -> None:
        while not self._stop_event.wait(0.5):
            time.sleep(0.1)
