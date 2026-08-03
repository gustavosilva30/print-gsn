from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class TemplateElement:
    type: str
    text: str | None = None
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    value: str | None = None


@dataclass(slots=True)
class Template:
    name: str
    elements: list[TemplateElement] = field(default_factory=list)

    def render(self, payload: dict[str, Any]) -> bytes:
        return b"template-render"
