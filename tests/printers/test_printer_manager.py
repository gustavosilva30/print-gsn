from app.services.print_manager import PrinterManager


def test_printer_manager_lists_default_printer() -> None:
    manager = PrinterManager()
    printers = manager.list_printers()
    assert isinstance(printers, list)
    assert printers


def test_printer_manager_sets_active_printer() -> None:
    manager = PrinterManager()
    printers = manager.list_printers()
    if printers:
        printer = manager.set_active_printer(printers[0].name)
        assert printer is not None
        assert manager.active_printer is not None
