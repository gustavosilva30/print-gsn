from __future__ import annotations

import platform
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.domain.job import PrintJob
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
            return [
                PrinterInfo(
                    name="Fake Printer",
                    driver="Generic",
                    is_default=True,
                    port="",
                    status="Ready",
                    type="Generic",
                )
            ]
        try:
            import win32print
        except Exception:  # noqa: BLE001
            return [
                PrinterInfo(
                    name="Fake Printer",
                    driver="Generic",
                    is_default=True,
                    port="",
                    status="Ready",
                    type="Generic",
                )
            ]
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

    def create_driver(
        self,
        printer: PrinterInfo,
        *,
        mock: bool = False,
        model: str = "OS-214 Plus",
        dpi: int = 203,
        darkness: int = 10,
        speed: int = 3,
        command_language: str = "PPLB",
    ) -> PrinterDriver:
        if printer.type == "Argox":
            from app.infrastructure.printers.argox import ArgoxPrinter

            return ArgoxPrinter(
                printer.name,
                mock=mock,
                model=model,
                dpi=dpi,
                darkness=darkness,
                speed=speed,
                command_language=command_language,
            )
        if printer.type == "Zebra":
            from app.infrastructure.printers.zebra import ZebraPrinter

            return ZebraPrinter(printer.name, mock=mock)
        if printer.type == "Brother":
            from app.infrastructure.printers.brother import BrotherPrinter

            return BrotherPrinter(printer.name, mock=mock)
        if printer.type == "Elgin":
            from app.infrastructure.printers.elgin import ElginPrinter

            return ElginPrinter(printer.name, mock=mock)
        from app.infrastructure.printers.windows_generic import WindowsGenericPrinter

        return WindowsGenericPrinter(printer.name, mock=mock)

    def print_job(
        self,
        job: PrintJob,
        *,
        mock: bool = False,
        default_printer: str = "",
        printer_type: str = "Argox",
        paper_width: int = 50,
        paper_height: int = 30,
        label_language: str = "PPLB",
        command_language: str = "PPLB",
        argox_model: str = "OS-214 Plus",
        argox_dpi: int = 203,
        argox_darkness: int = 10,
        argox_speed: int = 3,
    ) -> None:
        """Build label payload from job data and send it to the resolved printer.

        Raises on failure so the caller can mark the job as FAILED.
        """
        printer = self._resolve_job_printer(
            job.printer_name,
            default_printer=default_printer,
            printer_type=printer_type,
            mock=mock,
        )
        if printer is None:
            raise RuntimeError("No printer available for job")

        self.active_printer = printer
        self.default_printer_name = printer.name

        effective_language = command_language or label_language or "PPLB"
        payload = self._build_payload_from_job(
            job,
            paper_width=paper_width,
            paper_height=paper_height,
            label_language=effective_language,
            dpi=argox_dpi,
            darkness=argox_darkness,
            speed=argox_speed,
        )
        if not payload:
            raise ValueError("Empty print payload")

        driver = self.create_driver(
            printer,
            mock=mock,
            model=argox_model,
            dpi=argox_dpi,
            darkness=argox_darkness,
            speed=argox_speed,
            command_language=effective_language,
        )
        driver.connect()
        try:
            copies = max(1, int(job.copies or 1))
            for _ in range(copies):
                driver.print_label(payload)
            self._log("job", printer, "success", payload=payload)
        except Exception as exc:  # noqa: BLE001
            self._log("job", printer, "error", payload=payload, error=str(exc))
            raise
        finally:
            driver.disconnect()

    def print_test(self, printer_name: str | None = None, *, mock: bool = False) -> bool:
        printer = self._resolve_printer(printer_name)
        if printer is None:
            return False
        self.active_printer = printer
        self.default_printer_name = printer.name
        driver = self.create_driver(printer, mock=mock)
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
        mock: bool = False,
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
        driver = self.create_driver(printer, mock=mock)
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
                    f"Printer: {printer.name} | driver={printer.driver} | port={printer.port} | "
                    f"status={printer.status} | type={printer.type} | default={printer.is_default}\n"
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

    def _resolve_job_printer(
        self,
        printer_name: str | None,
        *,
        default_printer: str,
        printer_type: str,
        mock: bool,
    ) -> PrinterInfo | None:
        name = (printer_name or default_printer or "").strip()
        printers = self.list_printers()
        if name:
            for printer in printers:
                if printer.name == name:
                    return printer
            # Named printer not discovered (common in mock / non-Windows): synthesize one
            if mock or platform.system() != "Windows":
                return PrinterInfo(
                    name=name,
                    driver=printer_type,
                    is_default=True,
                    port="",
                    status="Ready",
                    type=self._normalize_type(printer_type),
                )
            return None
        resolved = self.get_default_printer() or (printers[0] if printers else None)
        if resolved is None and (mock or platform.system() != "Windows"):
            return PrinterInfo(
                name=default_printer or "Mock Printer",
                driver=printer_type,
                is_default=True,
                port="",
                status="Ready",
                type=self._normalize_type(printer_type),
            )
        return resolved

    def _resolve_printer(self, printer_name: str | None = None) -> PrinterInfo | None:
        printers = self.list_printers()
        if printer_name:
            for printer in printers:
                if printer.name == printer_name:
                    return printer
            return None
        return self.get_default_printer() or (printers[0] if printers else None)

    def _build_payload_from_job(
        self,
        job: PrintJob,
        *,
        paper_width: int,
        paper_height: int,
        label_language: str,
        dpi: int = 203,
        darkness: int = 10,
        speed: int = 3,
    ) -> bytes:
        data = job.payload or {}
        # Accept raw bytes already prepared by upstream systems
        raw = data.get("raw") or data.get("raw_payload")
        if isinstance(raw, (bytes, bytearray)):
            return bytes(raw)
        if isinstance(raw, str) and raw.strip():
            return raw.encode("utf-8")

        # Accept pre-built command string (ZPL / PPLA / PPLB)
        commands = data.get("commands") or data.get("zpl") or data.get("pplb") or data.get("ppla")
        if isinstance(commands, str) and commands.strip():
            return commands.encode("utf-8")
        if isinstance(commands, (bytes, bytearray)):
            return bytes(commands)

        company = str(
            data.get("company")
            or data.get("empresa")
            or data.get("company_name")
            or ""
        )
        product = str(data.get("product") or data.get("produto") or data.get("descricao") or "")
        code = str(data.get("code") or data.get("codigo") or data.get("sku") or "")
        ean = str(data.get("ean") or data.get("barcode") or data.get("gtin") or code)
        qrcode = str(data.get("qrcode") or data.get("qr") or code)
        price = str(data.get("price") or data.get("preco") or "")
        description = str(data.get("description") or data.get("descricao") or product)
        size = str(data.get("size") or f"{paper_width}x{paper_height}")
        language = str(data.get("language") or data.get("label_language") or label_language or "PPLB")
        # Map UI language PT-BR to engine language when needed
        if language.upper() in {"PT-BR", "PT", "BR"}:
            language = "PPLB"

        builder = LabelBuilder(dpi=dpi)
        return builder.build(
            company=company or "GSN",
            product=product or job.template or "Label",
            code=code or job.id[:8],
            ean=ean or code or "0000000000000",
            qrcode=qrcode or code or job.id,
            price=price or "-",
            description=description or product or "",
            size=size,
            language=language,
            darkness=darkness,
            speed=speed,
        )

    def _log(
        self,
        action: str,
        printer: PrinterInfo,
        result: str,
        payload: bytes | None = None,
        error: str | None = None,
    ) -> None:
        log_path = self.base_dir / "logs" / "printer_operations.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(
                f"{timestamp} | action={action} | printer={printer.name} | result={result} | "
                f"payload={payload.decode('utf-8', errors='ignore') if payload else ''} | "
                f"error={error or ''}\n"
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

    def _normalize_type(self, printer_type: str) -> str:
        normalized = (printer_type or "Generic").strip()
        mapping = {
            "argox": "Argox",
            "zebra": "Zebra",
            "brother": "Brother",
            "elgin": "Elgin",
            "generic": "Generic",
            "windows": "Generic",
            "windows generic": "Generic",
        }
        return mapping.get(normalized.lower(), normalized if normalized in mapping.values() else "Generic")

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
