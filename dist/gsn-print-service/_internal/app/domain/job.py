from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4


class JobStatus(str, Enum):
    PENDING = "Pending"
    DOWNLOADING = "Downloading"
    PROCESSING = "Processing"
    PRINTING = "Printing"
    PRINTED = "Printed"
    FAILED = "Failed"
    CANCELED = "Canceled"


@dataclass(slots=True)
class PrintJob:
    id: str = field(default_factory=lambda: str(uuid4()))
    printer_name: str = ""
    template: str = "default"
    payload: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    copies: int = 1
    status: JobStatus = JobStatus.PENDING
    remote_message_id: str | None = None
    external_job_id: str | None = None
    company_id: str | None = None
    created_at: str = ""
    updated_at: str = ""
    error: str | None = None
