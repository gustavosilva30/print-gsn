from app.application.application_container import ApplicationContainer
from app.config.settings import Settings


def test_container_builds_services() -> None:
    container = ApplicationContainer(Settings(), stop_event=None)
    services = container.build()
    assert services.print_service is not None
    assert services.websocket_client is not None
    assert services.printer_manager is not None
