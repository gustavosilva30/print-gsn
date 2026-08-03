from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.domain.job import JobStatus, PrintJob


class SQLiteJobRepository:
    def __init__(self, db_path: Path | None = None) -> None:
        self._db_path = db_path or Path(__file__).resolve().parents[3] / "app" / "database" / "jobs.sqlite3"
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    printer_name TEXT NOT NULL,
                    template TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    copies INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    error TEXT
                )
                """
            )
            conn.commit()

    def save(self, job: PrintJob) -> None:
        now = datetime.now(timezone.utc).isoformat()
        if not job.created_at:
            job.created_at = now
        job.updated_at = now
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                INSERT INTO jobs (id, printer_name, template, payload, copies, status, created_at, updated_at, error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job.id,
                    job.printer_name,
                    job.template,
                    str(job.payload),
                    job.copies,
                    job.status.value,
                    job.created_at,
                    job.updated_at,
                    job.error,
                ),
            )
            conn.commit()

    def list_by_status(self, status: JobStatus) -> list[PrintJob]:
        with sqlite3.connect(self._db_path) as conn:
            rows = conn.execute(
                "SELECT id, printer_name, template, payload, copies, status, created_at, updated_at, error FROM jobs WHERE status = ?",
                (status.value,),
            ).fetchall()
        return [self._row_to_job(row) for row in rows]

    def update_status(self, job_id: str, status: JobStatus, error: str | None = None) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                "UPDATE jobs SET status = ?, updated_at = ?, error = ? WHERE id = ?",
                (status.value, now, error, job_id),
            )
            conn.commit()

    def _row_to_job(self, row: tuple[Any, ...]) -> PrintJob:
        return PrintJob(
            id=row[0],
            printer_name=row[1],
            template=row[2],
            payload={"value": row[3]},
            copies=row[4],
            status=JobStatus(row[5]),
            created_at=row[6],
            updated_at=row[7],
            error=row[8],
        )
