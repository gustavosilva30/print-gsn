from __future__ import annotations

from pathlib import Path

import pytest

from app.application.services.job_service import JobService
from app.config.settings import Settings
from app.domain.job import JobStatus, PrintJob
from app.infrastructure.repository.sqlite_repository import SQLiteJobRepository
from app.infrastructure.websocket.messages import ProtocolEnvelope
from app.services.print_manager import PrinterManager
from app.services.print_service import PrintService


def _make_settings(tmp_path: Path) -> Settings:
    settings = Settings()
    settings.base_dir = tmp_path
    settings.mock_mode = True
    settings.default_printer = "Mock Argox"
    settings.printer_type = "Argox"
    settings.protocol_version = "1.0"
    settings.computer_id = "test-computer"
    settings.company_id = "test-company"
    settings.token = "test-token"
    return settings


def test_process_job_prints_and_marks_printed(tmp_path: Path) -> None:
    settings = _make_settings(tmp_path)
    repo = SQLiteJobRepository(tmp_path / "jobs.sqlite3")
    job_service = JobService(repo)
    manager = PrinterManager(base_dir=tmp_path)
    sent: list[ProtocolEnvelope] = []

    service = PrintService(
        job_service=job_service,
        printer_manager=manager,
        settings=settings,
        send_callback=sent.append,
    )

    job = PrintJob(
        printer_name="Mock Argox",
        template="default",
        payload={
            "codigo": "SKU-001",
            "descricao": "Produto Teste",
            "preco": "19,90",
            "company": "GSN",
        },
        copies=1,
        external_job_id="crm-100",
        remote_message_id="msg-100",
    )
    job_service.enqueue(job)

    service.process_job(job)

    updated = job_service.get_by_id(job.id)
    assert updated is not None
    assert updated.status == JobStatus.PRINTED
    assert len(sent) == 1
    assert sent[0].type == "completed"
    assert sent[0].payload["job_id"] == job.id
    assert sent[0].payload["status"] == "printed"

    mock_dir = tmp_path / "logs" / "mock_print_jobs"
    # BasePrinter saves under app/logs relative to package; also check operations log
    operations = tmp_path / "logs" / "printer_operations.log"
    assert operations.exists()
    content = operations.read_text(encoding="utf-8")
    assert "result=success" in content


def test_process_job_failure_notifies_failed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    settings = _make_settings(tmp_path)
    repo = SQLiteJobRepository(tmp_path / "jobs.sqlite3")
    job_service = JobService(repo)
    manager = PrinterManager(base_dir=tmp_path)
    sent: list[ProtocolEnvelope] = []

    def _fail(self, *args, **kwargs):
        raise RuntimeError("Printer offline")

    monkeypatch.setattr(PrinterManager, "print_job", _fail)

    service = PrintService(
        job_service=job_service,
        printer_manager=manager,
        settings=settings,
        send_callback=sent.append,
    )

    job = PrintJob(
        printer_name="Broken",
        payload={"codigo": "X"},
        remote_message_id="msg-fail",
    )
    job_service.enqueue(job)
    service.process_job(job)

    updated = job_service.get_by_id(job.id)
    assert updated is not None
    assert updated.status == JobStatus.FAILED
    assert updated.error == "Printer offline"
    assert len(sent) == 1
    assert sent[0].type == "failed"
    assert sent[0].payload["code"] == "PRINT_ERROR"
    assert sent[0].payload["reason"] == "Printer offline"


def test_print_manager_builds_payload_from_job_fields(tmp_path: Path) -> None:
    manager = PrinterManager(base_dir=tmp_path)
    job = PrintJob(
        printer_name="Mock Argox",
        payload={
            "company": "ACME",
            "product": "Caixa",
            "codigo": "C-99",
            "preco": "9,90",
        },
        copies=2,
    )
    manager.print_job(
        job,
        mock=True,
        default_printer="Mock Argox",
        printer_type="Argox",
        paper_width=50,
        paper_height=30,
        label_language="PPLB",
    )
    log = (tmp_path / "logs" / "printer_operations.log").read_text(encoding="utf-8")
    assert "result=success" in log
    assert "ACME" in log or "C-99" in log


def test_print_manager_accepts_raw_commands(tmp_path: Path) -> None:
    manager = PrinterManager(base_dir=tmp_path)
    raw = b"^XA^FO50,50^FDRAW-TEST^FS^XZ"
    job = PrintJob(printer_name="Mock", payload={"raw": raw.decode("utf-8")})
    manager.print_job(job, mock=True, default_printer="Mock", printer_type="Generic")
    log = (tmp_path / "logs" / "printer_operations.log").read_text(encoding="utf-8")
    assert "RAW-TEST" in log
