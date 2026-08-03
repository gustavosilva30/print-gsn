from __future__ import annotations

from app.infrastructure.printers.argox import ArgoxPrinter, resolve_argox_profile
from app.services.label_builder import LabelBuilder


def test_resolve_argox_profile_os214_plus() -> None:
    profile = resolve_argox_profile("OS-214 Plus")
    assert profile.model == "OS-214 Plus"
    assert profile.dpi == 203
    assert profile.max_width_mm == 104


def test_argox_driver_mock_print_test_pplb() -> None:
    printer = ArgoxPrinter("Argox OS-214 Plus", mock=True, model="OS-214 Plus", command_language="PPLB")
    printer.connect()
    printer.print_test()
    printer.disconnect()
    assert printer._payloads
    payload = printer._payloads[0]
    assert b"^XA" in payload
    assert b"GSN Print Service" in payload
    assert b"TESTE001" in payload
    assert b"^XZ" in payload


def test_argox_driver_mock_print_test_ppla() -> None:
    printer = ArgoxPrinter("Argox OS-214 Plus", mock=True, model="OS-214 Plus", command_language="PPLA")
    printer.connect()
    printer.print_test()
    assert printer._payloads
    payload = printer._payloads[0]
    assert b"I8,A,001" in payload
    assert b"GSN Print Service" in payload
    assert b"P1" in payload


def test_label_builder_pplb_contains_fields() -> None:
    builder = LabelBuilder(dpi=203)
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
    assert b"ABC123" in payload
    assert b"^XZ" in payload


def test_label_builder_ppla_contains_fields() -> None:
    builder = LabelBuilder(dpi=203)
    payload = builder.build(
        company="GSN",
        product="Etiqueta",
        code="ABC123",
        ean="7891234567895",
        qrcode="ABC123",
        price="12,90",
        description="Produto teste",
        size="50x30",
        language="PPLA",
    )
    assert b"I8,A,001" in payload
    assert b"GSN" in payload
    assert b"ABC123" in payload
    assert b"P1" in payload


def test_settings_loads_argox_config() -> None:
    from app.config.settings import Settings

    settings = Settings()
    assert settings.printer_type == "Argox"
    assert settings.command_language == "PPLB"
    assert settings.argox_model == "OS-214 Plus"
    assert settings.argox_dpi == 203
