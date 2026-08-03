from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Any, Callable

from loguru import logger

if TYPE_CHECKING:
    from app.application.application import Application


def _create_default_icon():
    """Create a simple in-memory icon (no external asset required)."""
    try:
        from PIL import Image, ImageDraw

        image = Image.new("RGB", (64, 64), color=(20, 90, 160))
        draw = ImageDraw.Draw(image)
        draw.rectangle((12, 12, 52, 52), fill=(255, 255, 255))
        draw.rectangle((20, 28, 44, 36), fill=(20, 90, 160))
        return image
    except Exception:  # noqa: BLE001
        return None


class SystemTray:
    """System tray icon for GSN Print Service.

    Uses pystray when available. Falls back to a blocking wait loop so the
    process remains alive even without GUI dependencies.
    """

    def __init__(self, application: Application) -> None:
        self._app = application
        self._icon: Any | None = None
        self._running = False

    def run(self) -> None:
        self._running = True
        try:
            import pystray
            from pystray import Menu, MenuItem
        except Exception as exc:  # noqa: BLE001
            logger.warning("pystray unavailable ({exc}); running without tray UI", exc=exc)
            self._run_headless_fallback()
            return

        image = _create_default_icon()
        if image is None:
            logger.warning("Pillow icon unavailable; running without tray UI")
            self._run_headless_fallback()
            return

        menu = Menu(
            MenuItem("Status", self._show_status, default=True),
            MenuItem("Testar impressão", self._print_test),
            MenuItem("Configurações", self._open_settings),
            MenuItem("Guia de configuração", self._open_guide),
            Menu.SEPARATOR,
            MenuItem("Sair", self._on_exit),
        )
        self._icon = pystray.Icon("gsn-print-service", image, "GSN Print Service", menu)
        logger.info("System tray started")
        self._icon.run()

    def stop(self) -> None:
        self._running = False
        if self._icon is not None:
            try:
                self._icon.stop()
            except Exception:  # noqa: BLE001
                pass

    def _run_headless_fallback(self) -> None:
        logger.info("Tray fallback: waiting for stop signal")
        while self._running and not self._app._stop_event.is_set():
            self._app._stop_event.wait(1.0)

    def _show_status(self, icon: Any | None = None, item: Any | None = None) -> None:
        status = self._app.status()
        message = (
            f"GSN Print Service v{status.get('service_version', '?')}\n"
            f"Servidor: {status.get('server_url')}\n"
            f"Impressora: {status.get('default_printer') or '(não definida)'}\n"
            f"Fila: {status.get('pending_jobs')} job(s)\n"
            f"WebSocket: {'ativo' if status.get('websocket_running') else 'parado'}\n"
            f"Mock: {'sim' if status.get('mock_mode') else 'não'}"
        )
        logger.info("Status tray:\n{message}", message=message)
        self._notify("Status", message)

    def _print_test(self, icon: Any | None = None, item: Any | None = None) -> None:
        def worker() -> None:
            ok = self._app.request_print_test()
            self._notify(
                "Teste de impressão",
                "Impressão de teste enviada com sucesso." if ok else "Falha no teste de impressão. Veja os logs.",
            )

        threading.Thread(target=worker, daemon=True, name="tray-print-test").start()

    def _open_guide(self, icon=None, item=None) -> None:
        def worker() -> None:
            try:
                from app.ui.windows.guide_window import GuideWindow
                GuideWindow().show()
            except Exception as exc:
                logger.exception("Failed to open guide: {exc}", exc=exc)
                self._notify("Guia", f"Não foi possível abrir: {exc}")

        threading.Thread(target=worker, daemon=True, name="tray-guide").start()

    def _open_settings(self, icon: Any | None = None, item: Any | None = None) -> None:
        def worker() -> None:
            try:
                from app.ui.windows.settings_window import SettingsWindow

                SettingsWindow(self._app.settings).show()
            except Exception as exc:  # noqa: BLE001
                logger.exception("Failed to open settings: {exc}", exc=exc)
                self._notify("Configurações", f"Não foi possível abrir: {exc}")

        threading.Thread(target=worker, daemon=True, name="tray-settings").start()

    def _on_exit(self, icon: Any | None = None, item: Any | None = None) -> None:
        logger.info("Exit requested from tray")
        self._app.stop()
        self.stop()

    def _notify(self, title: str, message: str) -> None:
        if self._icon is not None and hasattr(self._icon, "notify"):
            try:
                self._icon.notify(message, title)
                return
            except Exception:  # noqa: BLE001
                pass
        logger.info("{title}: {message}", title=title, message=message)
