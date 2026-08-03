from __future__ import annotations

import threading
import time
from typing import Protocol


class Lifecycle(Protocol):
    def start(self) -> None:
        ...

    def stop(self) -> None:
        ...


class LifecycleManager:
    def __init__(self, stop_event: threading.Event) -> None:
        self._stop_event = stop_event
        self._components: list[Lifecycle] = []

    def register(self, component: Lifecycle) -> None:
        self._components.append(component)

    def start(self) -> None:
        for component in self._components:
            component.start()

    def stop(self) -> None:
        for component in self._components:
            component.stop()
        self._stop_event.set()

    def wait(self) -> None:
        while not self._stop_event.wait(0.5):
            time.sleep(0.1)
