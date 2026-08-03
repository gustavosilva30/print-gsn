from __future__ import annotations

from types import SimpleNamespace

from app.application.services.job_service import JobService
from app.config.settings import Settings
from app.core.logging import configure_logging
from app.infrastructure.repository.sqlite_repository import SQLiteJobRepository
from app.infrastructure.websocket.client import WebSocketClient
from app.services.print_service import PrintService


def bootstrap_application(settings: Settings, stop_event: object | None = None) -> object:
    configure_logging(settings.base_dir)
    repository = SQLiteJobRepository(settings.base_dir / "database" / "jobs.sqlite3")
    job_service = JobService(repository)
    print_service = PrintService(job_service, stop_event=stop_event)
    websocket_client = WebSocketClient(settings, job_service, print_service, stop_event=stop_event)
    websocket_client.connect()
    print_service.start()
    return SimpleNamespace(print_service=print_service, websocket_client=websocket_client)
