from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from app.ui.tray.tray import SystemTray, _create_default_icon


def test_create_default_icon_or_none() -> None:
    # May return None if Pillow missing; should not raise
    icon = _create_default_icon()
    assert icon is None or icon.size == (64, 64)


def test_tray_fallback_exits_on_stop() -> None:
    stop_event = __import__("threading").Event()
    app = SimpleNamespace(
        _stop_event=stop_event,
        status=lambda: {"service_version": "0.1.0"},
        stop=MagicMock(),
        request_print_test=MagicMock(return_value=True),
        settings=SimpleNamespace(),
    )
    tray = SystemTray(application=app)  # type: ignore[arg-type]
    stop_event.set()
    tray._run_headless_fallback()
