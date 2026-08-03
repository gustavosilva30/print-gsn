from __future__ import annotations

from app.infrastructure.printers.base import BasePrinter


class ArgoxPrinter(BasePrinter):
    def __init__(self, name: str) -> None:
        super().__init__(name)

    def print(self, job: object) -> None:
        return None
