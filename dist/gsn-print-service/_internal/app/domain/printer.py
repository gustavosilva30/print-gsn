from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(slots=True)
class PrinterInfo:
    name: str
    driver: str
    is_default: bool = False


class PrinterDriver(Protocol):
    def connect(self) -> None:
        ...

    def disconnect(self) -> None:
        ...

    def print(self, job: object) -> None:
        ...

    def status(self) -> str:
        ...

    def cancel(self) -> None:
        ...
