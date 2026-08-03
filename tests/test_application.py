import threading
from types import SimpleNamespace

from app.application.application import Application


class FakeService:
    def __init__(self) -> None:
        self.stopped = False

    def stop(self) -> None:
        self.stopped = True


def test_application_stop_cleans_up_services() -> None:
    app = Application()
    app._stop_event = threading.Event()
    app._services = SimpleNamespace(
        print_service=FakeService(),
        websocket_client=FakeService(),
    )

    app.stop()

    assert app._stop_event.is_set()
    assert app._services.print_service.stopped
    assert app._services.websocket_client.stopped
