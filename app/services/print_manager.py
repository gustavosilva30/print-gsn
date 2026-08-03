from __future__ import annotations

import json
import platform
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from app.domain.printer import PrinterDriver, PrinterInfo
from app.services.label_builder import LabelBuilder


@dataclass(slots=True)
class PrinterManager:
    default_printer_name: str | None = None
    active_printer: PrinterInfo | None = None
    driver_map: dict[str, type[PrinterDriver]] | None = None
    base_dir: Path | None = None

    def __post_init__(self) -> None:
        self.base_dir = self.base_dir or Path(__file__).resolve().parents[1]
        self.driver_map = {
            "Argox": self._build_argox_driver,
            "Zebra": self._build_zebra_driver,
            "Brother": self._build_brother_driver,
            "Elgin": self._build_elgin_driver,
            "Generic": self._build_generic_driver,
        }

    def list_printers(self) -> list[PrinterInfo]:
        if platform.system() != "Windows":
            return [PrinterInfo(name="Fake Printer", driver="Generic", is_default=True, port="", status="Ready", type="Generic")]
        try:
            import win32print
        except Exception:  # noqa: BLE001
            return [PrinterInfo(name="Fake Printer", driver="Generic", is_default=True, port="", status="Ready", type="Generic")]
        printers = []
        default_printer = win32print.GetDefaultPrinter()
        for printer_name in win32print.EnumPrinters(2):
            printer_info = PrinterInfo(
                name=printer_name[2],
                driver=printer_name[3],
                port="",
                is_default=printer_name[2] == default_printer,
                status="Ready",
                type=self._detect_driver(printer_name[3], printer_name[2]),
            )
            printers.append(printer_info)
        return printers

    def get_default_printer(self) -> PrinterInfo | None:
        printers = self.list_printers()
        for printer in printers:
            if printer.is_default:
                return printer
        return printers[0] if printers else None

    def set_active_printer(self, printer_name: str) -> PrinterInfo | None:
        printers = self.list_printers()
        for printer in printers:
            if printer.name == printer_name:
                self.active_printer = printer
                self.default_printer_name = printer_name
                return printer
        return None

    def validate_printer(self, printer_name: str) -> bool:
        return any(printer.name == printer_name for printer in self.list_printers())

    def create_driver(self, printer: PrinterInfo) -> PrinterDriver:
        if printer.type == "Argox":
            from app.infrastructure.printers.argox import ArgoxPrinter
            return ArgoxPrinter(printer.name)
        if printer.type == "Zebra":
            from app.infrastructure.printers.zebra import ZebraPrinter
            return ZebraPrinter(printer.name)
        if printer.type == "Brother":
            from app.infrastructure.printers.brother import BrotherPrinter
            return BrotherPrinter(printer.name)
        if printer.type == "Elgin":
            from app.infrastructure.printers.elgin import ElginPrinter
            return ElginPrinter(printer.name)
        from app.infrastructure.printers.windows_generic import WindowsGenericPrinter
        return WindowsGenericPrinter(printer.name)

    def print_test(self, printer_name: str | None = None) -> bool:
        printer = self._resolve_printer(printer_name)
        if printer is None:
            return False
        self.active_printer = printer
        self.default_printer_name = printer.name
        driver = self.create_driver(printer)
        driver.connect()
        try:
            driver.print_test()
            self._log("print", printer, "success", payload=b"TEST")
            return True
        except Exception as exc:  # noqa: BLE001
            self._log("print", printer, "error", error=str(exc))
            return False
        finally:
            driver.disconnect()

    def print_label(
        self,
        *,
        company: str,
        product: str,
        code: str,
        ean: str,
        qrcode: str,
        price: str,
        description: str,
        size: str = "50x30",
        language: str = "PPLB",
        printer_name: str | None = None,
    ) -> bool:
        printer = self._resolve_printer(printer_name)
        if printer is None:
            return False
        builder = LabelBuilder()
        payload = builder.build(
            company=company,
            product=product,
            code=code,
            ean=ean,
            qrcode=qrcode,
            price=price,
            description=description,
            size=size,
            language=language,
        )
        driver = self.create_driver(printer)
        driver.connect()
        try:
            driver.print_label(payload)
            self._log("label", printer, "success", payload=payload)
            return True
        except Exception as exc:  # noqa: BLE001
            self._log("label", printer, "error", error=str(exc))
            return False
        finally:
            driver.disconnect()

    def diagnose(self) -> dict[str, Any]:
        python_version = sys.version.split()[0]
        win32print_available = False
        pywin32_installed = False
        try:
            import win32print  # noqa: F401
            win32print_available = True
            pywin32_installed = True
        except Exception:  # noqa: BLE001
            pywin32_installed = False
        printers = self.list_printers()
        default_printer = self.get_default_printer()
        return {
            "operating_system": platform.system(),
            "windows_version": platform.version(),
            "python_version": python_version,
            "printers": printers,
            "default_printer": default_printer,
            "win32print_available": win32print_available,
            "pywin32_installed": pywin32_installed,
        }

    def save_diagnostic_log(self, diagnostics: dict[str, Any], path: Path | None = None) -> Path:
        output_path = path or self.base_dir / "logs" / "printer_diagnostic.log"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as handle:
            handle.write("=== Printer Diagnostic ===\n")
            handle.write(f"OS: {diagnostics['operating_system']}\n")
            handle.write(f"Windows: {diagnostics['windows_version']}\n")
            handle.write(f"Python: {diagnostics['python_version']}\n")
            for printer in diagnostics.get("printers", []):
                handle.write(
                    f"Printer: {printer.name} | driver={printer.driver} | port={printer.port} | status={printer.status} | type={printer.type} | default={printer.is_default}\n"
                )
            default_printer = diagnostics.get("default_printer")
            if default_printer is not None:
                handle.write(f"Default Printer: {default_printer.name}\n")
            handle.write(f"Win32Print available: {diagnostics['win32print_available']}\n")
            handle.write(f"pywin32 installed: {diagnostics['pywin32_installed']}\n")
        return output_path

    def generate_preview(self, payload: bytes, output_dir: Path | None = None) -> tuple[Path, Path]:
        output_dir = output_dir or (self.base_dir / "logs")
        output_dir.mkdir(parents=True, exist_ok=True)
        png_path = output_dir / "preview.png"
        pdf_path = output_dir / "preview.pdf"
        png_path.write_bytes(b"PNG")
        pdf_path.write_bytes(b"%PDF-1.4\n% test preview")
        return png_path, pdf_path

    def _resolve_printer(self, printer_name: str | None = None) -> PrinterInfo | None:
        printers = self.list_printers()
        if printer_name:
            for printer in printers:
                if printer.name == printer_name:
                    return printer
            return None
        return self.get_default_printer() or (printers[0] if printers else None)

    def _log(self, action: str, printer: PrinterInfo, result: str, payload: bytes | None = None, error: str | None = None) -> None:
        log_path = self.base_dir / "logs" / "printer_operations.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(
                f"{datetime.utcnow().isoformat()} | action={action} | printer={printer.name} | result={result} | payload={payload.decode('utf-8', errors='ignore') if payload else ''} | error={error or ''}\n"
            )

    def _detect_driver(self, driver_name: str, printer_name: str) -> str:
        combined = f"{driver_name} {printer_name}".lower()
        if "argox" in combined:
            return "Argox"
        if "zebra" in combined:
            return "Zebra"
        if "brother" in combined:
            return "Brother"
        if "elgin" in combined:
            return "Elgin"
        return "Generic"

    def _build_argox_driver(self) -> PrinterDriver:
        from app.infrastructure.printers.argox import ArgoxPrinter
        return ArgoxPrinter("Argox")

    def _build_zebra_driver(self) -> PrinterDriver:
        from app.infrastructure.printers.zebra import ZebraPrinter
        return ZebraPrinter("Zebra")

    def _build_brother_driver(self) -> PrinterDriver:
        from app.infrastructure.printers.brother import BrotherPrinter
        return BrotherPrinter("Brother")

    def _build_elgin_driver(self) -> PrinterDriver:
        from app.infrastructure.printers.elgin import ElginPrinter
        return ElginPrinter("Elgin")

    def _build_generic_driver(self) -> PrinterDriver:
        from app.infrastructure.printers.windows_generic import WindowsGenericPrinter
        return WindowsGenericPrinter("Generic")
