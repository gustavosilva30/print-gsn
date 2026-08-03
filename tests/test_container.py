from app.application.application_container import ApplicationContainer
from app.config.settings import Settings


def test_container_builds_services() -> None:
    settings = Settings()
    settings.auto_reconnect = False
    settings.server_url = "ws://127.0.0.1:1"
    container = ApplicationContainer(settings, stop_event=None)
    services = container.build()
    try:
        assert services.print_service is not None
        assert services.websocket_client is not None
        assert services.printer_manager is not None
        assert hasattr(services.print_service, "_printer_manager")
        assert services.print_service._printer_manager is services.printer_manager
    finally:
        if hasattr(services.print_service, "stop"):
            services.print_service.stop()
        if hasattr(services.websocket_client, "stop"):
            services.websocket_client.stop()
        local_http = getattr(services, "local_http", None)
        if local_http is not None and hasattr(local_http, "stop"):
            local_http.stop()
