from __future__ import annotations

from app.domain.printer import PrinterDriver


class BasePrinter(PrinterDriver):
    def __init__(self, name: str) -> None:
        self.name = name

    def connect(self) -> None:
        return None

    def disconnect(self) -> None:
        return None

    def print(self, job: object) -> None:
        return None

    def status(self) -> str:
        return "Ready"

    def cancel(self) -> None:
        return None
