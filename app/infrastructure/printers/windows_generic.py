from __future__ import annotations

import platform

from app.infrastructure.printers.base import BasePrinter


class WindowsGenericPrinter(BasePrinter):
    def __init__(self, name: str, mock: bool = False) -> None:
        super().__init__(name, mock=mock)

    def print_raw(self, payload: bytes) -> None:
        if not payload:
            raise ValueError("No payload provided")
        if self._mock:
            self._payloads.append(payload)
            self._save_mock_payload(payload)
            return
        if platform.system() != "Windows":
            self._payloads.append(payload)
            self._save_mock_payload(payload)
            return
        try:
            import win32print
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"win32print is not available: {exc}") from exc
        hprinter = win32print.OpenPrinter(self.name)
        try:
            win32print.StartDocPrinter(hprinter, 1, ("GSN Print", None, "RAW"))
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
