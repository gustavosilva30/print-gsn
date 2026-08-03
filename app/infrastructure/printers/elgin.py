from __future__ import annotations

from app.infrastructure.printers.base import BasePrinter


class ElginPrinter(BasePrinter):
    def __init__(self, name: str, mock: bool = False) -> None:
        super().__init__(name, mock=mock)
