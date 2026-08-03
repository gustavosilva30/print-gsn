from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from app.domain.printer import PrinterInfo
from app.services.label_builder import LabelBuilder
from app.services.print_manager import PrinterManager


class FakeDriver:
    def __init__(self, name: str = "Fake") -> None:
        self.name = name
        self.connected = False
        self.payloads: list[bytes] = []

    def connect(self) -> None:
        self.connected = True

    def disconnect(self) -> None:
        self.connected = False

    def print_raw(self, payload: bytes) -> None:
        self.payloads.append(payload)

    def print_test(self) -> None:
        self.payloads.append(b"TEST")

    def print_label(self, payload: bytes | str | None = None) -> None:
        if isinstance(payload, str):
            payload = payload.encode("utf-8")
        self.payloads.append(payload or b"LABEL")

    def status(self) -> str:
        return "Ready" if self.connected else "Disconnected"


def test_print_manager_can_build_label_payload() -> None:
    builder = LabelBuilder()
    payload = builder.build(
        company="GSN",
        product="Etiqueta",
        code="ABC123",
        ean="7891234567895",
        qrcode="ABC123",
        price="12,90",
        description="Produto teste",
        size="50x30",
        language="PPLB",
    )
    assert b"^XA" in payload
    assert b"GSN" in payload


def test_print_manager_print_test_uses_selected_printer(monkeypatch: pytest.MonkeyPatch) -> None:
    manager = PrinterManager()
    fake_driver = FakeDriver("Fake")
    printer = PrinterInfo(name="Fake Printer", driver="Argox", is_default=True, type="Argox")

    monkeypatch.setattr(PrinterManager, "list_printers", lambda self: [printer])
    monkeypatch.setattr(PrinterManager, "create_driver", lambda self, selected_printer, mock=False: fake_driver)

    result = manager.print_test(printer_name="Fake Printer")

    assert result is True
    assert fake_driver.payloads
    assert b"TEST" in fake_driver.payloads[0]


def test_print_manager_generates_preview_files(tmp_path: Path) -> None:
    builder = LabelBuilder()
    payload = builder.build(
        company="GSN",
        product="Produto",
        code="XYZ",
        ean="7890000000000",
        qrcode="XYZ",
        price="5,00",
        description="Preview",
        size="60x40",
        language="PPLA",
    )
    output_dir = tmp_path
    png_path, pdf_path = PrinterManager().generate_preview(payload=payload, output_dir=output_dir)
    assert png_path.exists()
    assert pdf_path.exists()
