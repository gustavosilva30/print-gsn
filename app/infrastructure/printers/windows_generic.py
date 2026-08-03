from __future__ import annotations

import os
import platform

from app.infrastructure.printers.base import BasePrinter


class WindowsGenericPrinter(BasePrinter):
    def __init__(self, name: str, mock: bool = False) -> None:
        super().__init__(name, mock=mock)

    def print_raw(self, payload: bytes) -> None:
        if platform.system() != "Windows":
            return
        try:
            import win32print
            import win32ui
        except Exception:  # noqa: BLE001
            return
        if not payload:
            raise ValueError("No payload provided")
        printer_name = self.name
        hprinter = win32print.OpenPrinter(printer_name)
        try:
            hjob = win32print.StartDocPrinter(hprinter, 1, ("GSN Print", None, "RAW"))
            win32print.StartPagePrinter(hprinter)
            win32print.WritePrinter(hprinter, payload)
            win32print.EndPagePrinter(hprinter)
            win32print.EndDocPrinter(hprinter)
        finally:
            win32print.ClosePrinter(hprinter)

    def print_label(self, payload: bytes | str | None = None) -> None:
        if payload is None:
            payload = b""
        if isinstance(payload, str):
            payload = payload.encode("utf-8")
        self.print_raw(payload)
