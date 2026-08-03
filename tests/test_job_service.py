from app.application.services.job_service import JobService
from app.domain.job import JobStatus, PrintJob
from app.infrastructure.repository.sqlite_repository import SQLiteJobRepository


def test_enqueue_and_update_status(tmp_path):
    repository = SQLiteJobRepository(tmp_path / "jobs.sqlite3")
    service = JobService(repository)

    job = PrintJob(printer_name="Printer", template="peca", payload={"codigo": "1"}, copies=2)
    service.enqueue(job)
    assert service.get_pending_jobs()[0].id == job.id

    service.update_status(job.id, JobStatus.PRINTED)
    pending = service.get_pending_jobs()
    assert pending == []
