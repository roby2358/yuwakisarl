"""Rolling score tracker for recent deliveries."""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Deque, Dict


class RollingScore:
    """Tracks per-player delivery counts within a rolling time window."""

    def __init__(self, window_seconds: float) -> None:
        if window_seconds < 0:
            raise ValueError("window_seconds must be non-negative")
        self._window = float(window_seconds)
        self._events: Dict[int, Deque[float]] = defaultdict(deque)

    def record(self, player_identifier: int, timestamp: float, count: int = 1) -> None:
        if count <= 0:
            return
        events = self._events[player_identifier]
        for _ in range(count):
            events.append(float(timestamp))

    def total(self, player_identifier: int, current_time: float) -> int:
        self._purge(player_identifier, current_time)
        return len(self._events[player_identifier])

    def totals(self, current_time: float) -> Dict[int, int]:
        snapshot: Dict[int, int] = {}
        for identifier in list(self._events.keys()):
            total = self.total(identifier, current_time)
            if total:
                snapshot[identifier] = total
        return snapshot

    def reset(self) -> None:
        self._events.clear()

    def _purge(self, player_identifier: int, current_time: float) -> None:
        if self._window == 0.0:
            self._events[player_identifier].clear()
            return
        cutoff = current_time - self._window
        events = self._events[player_identifier]
        while events and events[0] < cutoff:
            events.popleft()


