from __future__ import annotations

from app.application.services.job_service import JobService
from app.config.settings import Settings
from app.core.logging import configure_logging
from app.infrastructure.repository.sqlite_repository import SQLiteJobRepository
from app.infrastructure.websocket.client import WebSocketClient
from app.services.print_service import PrintService


def bootstrap_application(settings: Settings) -> None:
    configure_logging(settings.base_dir)
    repository = SQLiteJobRepository(settings.base_dir / "database" / "jobs.sqlite3")
    job_service = JobService(repository)
    print_service = PrintService(job_service)
    websocket_client = WebSocketClient(settings, job_service, print_service)
    websocket_client.connect()
    print_service.start()
