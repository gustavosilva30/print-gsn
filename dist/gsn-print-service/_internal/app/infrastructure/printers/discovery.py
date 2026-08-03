from __future__ import annotations

import os
from typing import Any

from app.domain.printer import PrinterInfo


class PrinterDiscovery:
    def discover(self) -> list[PrinterInfo]:
        names = []
        for key in ["COMPUTERNAME", "HOSTNAME"]:
            value = os.getenv(key)
            if value:
                names.append(value)
        printers = [PrinterInfo(name=name, driver="Windows Generic", is_default=True) for name in names]
        return printers or [PrinterInfo(name="Default Printer", driver="Windows Generic", is_default=True)]
