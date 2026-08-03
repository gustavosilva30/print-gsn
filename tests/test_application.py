import threading
from types import SimpleNamespace

from app.application.application import Application


class FakeService:
    def __init__(self) -> None:
        self.stopped = False
        self._running = True

    def stop(self) -> None:
        self.stopped = True
        self._running = False


def test_application_stop_cleans_up_services() -> None:
    app = Application()
    app._stop_event = threading.Event()
    app._services = SimpleNamespace(
        print_service=FakeService(),
        websocket_client=FakeService(),
    )
    app._started = True

    app.stop()

    assert app._stop_event.is_set()
    assert app._services.print_service.stopped
    assert app._services.websocket_client.stopped


def test_application_status_snapshot() -> None:
    app = Application()
    app._services = SimpleNamespace(
        print_service=FakeService(),
        websocket_client=FakeService(),
        job_service=SimpleNamespace(count_pending_jobs=lambda: 2),
    )
    app._started = True
    status = app.status()
    assert status["started"] is True
    assert status["pending_jobs"] == 2
    assert status["websocket_running"] is True
