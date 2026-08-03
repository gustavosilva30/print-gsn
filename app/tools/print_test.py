from __future__ import annotations

from app.services.print_manager import PrinterManager


def main() -> None:
    manager = PrinterManager()
    printer = manager.get_default_printer()
    if printer is None:
        print("No printers found")
        return
    if printer.type.lower() == "argox":
        manager.print_test(printer_name=printer.name)
    else:
        print(f"Select a printer from: {[p.name for p in manager.list_printers()]}")


if __name__ == "__main__":
    main()
