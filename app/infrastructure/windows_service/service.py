from __future__ import annotations

import sys
import threading
from typing import Any

from loguru import logger

SERVICE_NAME = "GSNPrintService"
SERVICE_DISPLAY_NAME = "GSN Print Service"
SERVICE_DESCRIPTION = "Recebe jobs de impressão via WebSocket e imprime etiquetas térmicas localmente."


def is_windows() -> bool:
    return sys.platform.startswith("win")


def _require_pywin32() -> Any:
    try:
        import win32serviceutil  # noqa: F401
        import win32service  # noqa: F401
        import servicemanager  # noqa: F401
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(
            "pywin32 is required to install/run the Windows service. "
            "Install with: pip install pywin32"
        ) from exc


class GSNPrintWindowsService:
    """Windows Service host that runs Application in headless mode.

    Defined as a plain class; the actual win32serviceutil.ServiceFramework
    subclass is created only on Windows to keep imports safe on Linux/macOS.
    """

    _app: Any | None = None
    _thread: threading.Thread | None = None

    @classmethod
    def create_service_class(cls) -> type:
        _require_pywin32()
        import win32serviceutil
        import win32service
        import servicemanager

        class _Service(win32serviceutil.ServiceFramework):
            _svc_name_ = SERVICE_NAME
            _svc_display_name_ = SERVICE_DISPLAY_NAME
            _svc_description_ = SERVICE_DESCRIPTION

            def __init__(self, args: list[str]) -> None:
                win32serviceutil.ServiceFramework.__init__(self, args)
                self._stop_event = threading.Event()

            def SvcStop(self) -> None:  # noqa: N802
                self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
                self._stop_event.set()
                if cls._app is not None:
                    cls._app.stop()

            def SvcDoRun(self) -> None:  # noqa: N802
                servicemanager.LogMsg(
                    servicemanager.EVENTLOG_INFORMATION_TYPE,
                    servicemanager.PYS_SERVICE_STARTED,
                    (self._svc_name_, ""),
                )
                self.ReportServiceStatus(win32service.SERVICE_RUNNING)
                try:
                    from app.application.application import Application
                    from app.config.settings import Settings

                    settings = Settings()
                    settings.auto_reconnect = True
                    app = Application(settings)
                    cls._app = app
                    app.start()
                    while not self._stop_event.wait(1.0):
                        if app._stop_event.is_set():
                            break
                    app.shutdown()
                except Exception as exc:  # noqa: BLE001
                    logger.exception("Windows service failed: {exc}", exc=exc)
                    servicemanager.LogErrorMsg(str(exc))
                finally:
                    cls._app = None
                    self.ReportServiceStatus(win32service.SERVICE_STOPPED)

        return _Service


def install_service(exe_path: str | None = None) -> None:
    """Install the service (Windows only). Prefer running the frozen exe."""
    if not is_windows():
        raise RuntimeError("Windows Service can only be installed on Windows")
    _require_pywin32()
    import win32serviceutil

    service_class = GSNPrintWindowsService.create_service_class()
    sys.argv = [sys.argv[0], "install"]
    if exe_path:
        # Point service to a specific executable when packaged
        win32serviceutil.HandleCommandLine(
            service_class,
            argv=["", "install", f"--exe={exe_path}"],
        )
    else:
        win32serviceutil.HandleCommandLine(service_class)


def uninstall_service() -> None:
    if not is_windows():
        raise RuntimeError("Windows Service can only be uninstalled on Windows")
    _require_pywin32()
    import win32serviceutil

    service_class = GSNPrintWindowsService.create_service_class()
    sys.argv = [sys.argv[0], "remove"]
    win32serviceutil.HandleCommandLine(service_class)


def start_service() -> None:
    if not is_windows():
        raise RuntimeError("Windows Service can only be started on Windows")
    _require_pywin32()
    import win32serviceutil

    win32serviceutil.StartService(SERVICE_NAME)


def stop_service() -> None:
    if not is_windows():
        raise RuntimeError("Windows Service can only be stopped on Windows")
    _require_pywin32()
    import win32serviceutil

    win32serviceutil.StopService(SERVICE_NAME)


def run_service_host() -> None:
    """Entry point used when the process is launched by the Service Control Manager."""
    if not is_windows():
        raise RuntimeError("Service host is only available on Windows")
    _require_pywin32()
    import servicemanager
    import win32serviceutil

    service_class = GSNPrintWindowsService.create_service_class()
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(service_class)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(service_class)
