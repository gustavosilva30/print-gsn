from __future__ import annotations

from app.services.print_manager import PrinterManager


def main() -> None:
    manager = PrinterManager()
    diagnostics = manager.diagnose()
    log_path = manager.save_diagnostic_log(diagnostics)
    print(f"Diagnostic saved to {log_path}")


if __name__ == "__main__":
    main()
