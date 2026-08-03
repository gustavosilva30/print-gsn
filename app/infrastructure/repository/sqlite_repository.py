from __future__ import annotations

import json
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
                    metadata TEXT NOT NULL DEFAULT '{}',
                    copies INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    remote_message_id TEXT,
                    external_job_id TEXT,
                    company_id TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    error TEXT
                )
                """
            )
            self._ensure_columns(
                conn,
                {
                    "metadata": "TEXT NOT NULL DEFAULT '{}'",
                    "remote_message_id": "TEXT",
                    "external_job_id": "TEXT",
                    "company_id": "TEXT",
                },
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
                INSERT INTO jobs (
                    id,
                    printer_name,
                    template,
                    payload,
                    metadata,
                    copies,
                    status,
                    remote_message_id,
                    external_job_id,
                    company_id,
                    created_at,
                    updated_at,
                    error
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job.id,
                    job.printer_name,
                    job.template,
                    json.dumps(job.payload, ensure_ascii=True),
                    json.dumps(job.metadata, ensure_ascii=True),
                    job.copies,
                    job.status.value,
                    job.remote_message_id,
                    job.external_job_id,
                    job.company_id,
                    job.created_at,
                    job.updated_at,
                    job.error,
                ),
            )
            conn.commit()

    def list_by_status(self, status: JobStatus) -> list[PrintJob]:
        with sqlite3.connect(self._db_path) as conn:
            rows = conn.execute(
                """
                SELECT
                    id,
                    printer_name,
                    template,
                    payload,
                    metadata,
                    copies,
                    status,
                    remote_message_id,
                    external_job_id,
                    company_id,
                    created_at,
                    updated_at,
                    error
                FROM jobs
                WHERE status = ?
                """,
                (status.value,),
            ).fetchall()
        return [self._row_to_job(row) for row in rows]

    def get_by_id(self, job_id: str) -> PrintJob | None:
        return self._fetch_one("SELECT * FROM jobs WHERE id = ?", (job_id,))

    def get_by_remote_message_id(self, remote_message_id: str) -> PrintJob | None:
        return self._fetch_one("SELECT * FROM jobs WHERE remote_message_id = ?", (remote_message_id,))

    def get_by_external_job_id(self, external_job_id: str) -> PrintJob | None:
        return self._fetch_one("SELECT * FROM jobs WHERE external_job_id = ?", (external_job_id,))

    def update_status(self, job_id: str, status: JobStatus, error: str | None = None) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                "UPDATE jobs SET status = ?, updated_at = ?, error = ? WHERE id = ?",
                (status.value, now, error, job_id),
            )
            conn.commit()

    def _fetch_one(self, query: str, params: tuple[Any, ...]) -> PrintJob | None:
        with sqlite3.connect(self._db_path) as conn:
            row = conn.execute(query, params).fetchone()
        if row is None:
            return None
        return self._row_to_job(row)

    def _ensure_columns(self, conn: sqlite3.Connection, columns: dict[str, str]) -> None:
        existing_columns = {
            row[1]
            for row in conn.execute("PRAGMA table_info(jobs)").fetchall()
        }
        for column_name, column_definition in columns.items():
            if column_name in existing_columns:
                continue
            conn.execute(f"ALTER TABLE jobs ADD COLUMN {column_name} {column_definition}")

    def _row_to_job(self, row: tuple[Any, ...]) -> PrintJob:
        normalized_row = row
        if len(row) == 9:
            normalized_row = (
                row[0],
                row[1],
                row[2],
                row[3],
                "{}",
                row[4],
                row[5],
                None,
                None,
                None,
                row[6],
                row[7],
                row[8],
            )
        return PrintJob(
            id=normalized_row[0],
            printer_name=normalized_row[1],
            template=normalized_row[2],
            payload=self._loads_json(normalized_row[3]),
            metadata=self._loads_json(normalized_row[4]),
            copies=normalized_row[5],
            status=JobStatus(normalized_row[6]),
            remote_message_id=normalized_row[7],
            external_job_id=normalized_row[8],
            company_id=normalized_row[9],
            created_at=normalized_row[10],
            updated_at=normalized_row[11],
            error=normalized_row[12],
        )

    def _loads_json(self, raw_value: Any) -> dict[str, Any]:
        if isinstance(raw_value, dict):
            return raw_value
        if raw_value in (None, ""):
            return {}
        if isinstance(raw_value, str):
            try:
                loaded = json.loads(raw_value)
            except json.JSONDecodeError:
                return {"value": raw_value}
            if isinstance(loaded, dict):
                return loaded
        return {"value": raw_value}
