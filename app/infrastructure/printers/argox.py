from __future__ import annotations

import datetime as dt

from app.infrastructure.printers.base import BasePrinter


class ArgoxPrinter(BasePrinter):
    def __init__(self, name: str, mock: bool = False) -> None:
        super().__init__(name, mock=mock)

    def connect(self) -> None:
        self._connected = True

    def disconnect(self) -> None:
        self._connected = False

    def print_raw(self, payload: bytes) -> None:
        if not self._connected:
            raise RuntimeError("Printer is not connected")
        if not payload:
            raise ValueError("No payload provided")

    def print_test(self) -> None:
        self.print_label(self._build_test_label())

    def print_label(self, payload: bytes | str | None = None) -> None:
        if not self._connected:
            raise RuntimeError("Printer is not connected")
        if payload is None:
            payload = self._build_test_label()
        if isinstance(payload, str):
            payload = payload.encode("utf-8")
        self.print_raw(payload)

    def status(self) -> str:
        return "Ready" if self._connected else "Disconnected"

    def _build_test_label(self) -> str:
        now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return (
            "------------------------------\n"
            "GSN Print Service\n"
            "Teste de Impressão\n"
            f"Data/Hora: {now}\n"
            "Código: TESTE001\n"
            "------------------------------"
        )
