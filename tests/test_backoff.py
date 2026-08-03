from __future__ import annotations

from app.infrastructure.websocket.backoff import ExponentialBackoff


def test_backoff_starts_at_initial_delay() -> None:
    backoff = ExponentialBackoff(initial_delay_seconds=1, max_delay_seconds=30)
    assert backoff.next_delay() == 1.0


def test_backoff_increases_exponentially() -> None:
    backoff = ExponentialBackoff(initial_delay_seconds=1, max_delay_seconds=30, multiplier=2.0)
    delays = [backoff.next_delay() for _ in range(5)]
    assert delays == [1.0, 2.0, 4.0, 8.0, 16.0]


def test_backoff_caps_at_max_delay() -> None:
    backoff = ExponentialBackoff(initial_delay_seconds=1, max_delay_seconds=5, multiplier=2.0)
    delays = [backoff.next_delay() for _ in range(5)]
    assert delays == [1.0, 2.0, 4.0, 5.0, 5.0]


def test_backoff_reset_restores_initial_delay() -> None:
    backoff = ExponentialBackoff(initial_delay_seconds=2, max_delay_seconds=60)
    backoff.next_delay()
    backoff.next_delay()
    backoff.reset()
    assert backoff.next_delay() == 2.0
