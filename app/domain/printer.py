from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(slots=True)
class PrinterInfo:
    name: str
    driver: str
    is_default: bool = False
    port: str = ""
    status: str = "Ready"
    type: str = "Generic"


class PrinterDriver(Protocol):
    def connect(self) -> None:
        ...

    def disconnect(self) -> None:
        ...

    def print_raw(self, payload: bytes) -> None:
        ...

    def print_test(self) -> None:
        ...

    def print_label(self, payload: bytes | str | None = None) -> None:
        ...

    def status(self) -> str:
        ...
