from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ExponentialBackoff:
    initial_delay_seconds: float
    max_delay_seconds: float
    multiplier: float = 2.0
    _current_delay_seconds: float = field(init=False)

    def __post_init__(self) -> None:
        self._current_delay_seconds = self.initial_delay_seconds

    def next_delay(self) -> float:
        delay = self._current_delay_seconds
        next_delay = max(self.initial_delay_seconds, delay * self.multiplier)
        self._current_delay_seconds = min(self.max_delay_seconds, next_delay)
        return delay

    def reset(self) -> None:
        self._current_delay_seconds = self.initial_delay_seconds
