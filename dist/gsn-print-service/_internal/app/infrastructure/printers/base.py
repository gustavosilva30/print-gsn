from __future__ import annotations

from pathlib import Path

from app.domain.printer import PrinterDriver


class BasePrinter(PrinterDriver):
    def __init__(self, name: str, mock: bool = False) -> None:
        self.name = name
        self._connected = False
        self._mock = mock
        self._payloads: list[bytes] = []

    def connect(self) -> None:
        self._connected = True

    def disconnect(self) -> None:
        self._connected = False

    def print_raw(self, payload: bytes) -> None:
        if self._mock:
            self._payloads.append(payload)
            self._save_mock_payload(payload)
            return
        raise NotImplementedError("print_raw is not implemented")

    def print_test(self) -> None:
        self.print_label(None)

    def print_label(self, payload: bytes | str | None = None) -> None:
        if payload is None:
            payload = b""
        if isinstance(payload, str):
            payload = payload.encode("utf-8")
        self.print_raw(payload)

    def status(self) -> str:
        return "Ready" if self._connected else "Disconnected"

    def _save_mock_payload(self, payload: bytes) -> None:
        log_dir = Path(__file__).resolve().parents[3] / "app" / "logs" / "mock_print_jobs"
        log_dir.mkdir(parents=True, exist_ok=True)
        import time
        filename = f"mock_{self.name.replace(' ', '_')}_{int(time.monotonic_ns())}.zpl"
        (log_dir / filename).write_bytes(payload)
