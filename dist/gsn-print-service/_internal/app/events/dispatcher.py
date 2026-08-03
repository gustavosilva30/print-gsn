from __future__ import annotations

from app.models.event import Event


class EventDispatcher:
    def __init__(self) -> None:
        self._handlers: list[callable] = []

    def subscribe(self, handler: callable) -> None:
        self._handlers.append(handler)

    def dispatch(self, event: Event) -> None:
        for handler in self._handlers:
            handler(event)
