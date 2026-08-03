from __future__ import annotations

from app.infrastructure.printers.base import BasePrinter


class PrinterRegistry:
    def __init__(self) -> None:
        self._printers: dict[str, BasePrinter] = {}

    def register(self, printer: BasePrinter) -> None:
        self._printers[printer.name] = printer

    def list(self) -> list[BasePrinter]:
        return list(self._printers.values())
