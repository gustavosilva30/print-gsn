from app.infrastructure.printers.discovery import PrinterDiscovery


def test_discover_returns_printer_info():
    discovery = PrinterDiscovery()
    printers = discovery.discover()
    assert printers
    assert printers[0].name
