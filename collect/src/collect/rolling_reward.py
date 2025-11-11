"""Rolling reward tracker aggregated by whole seconds within a sliding window."""

from __future__ import annotations

import math
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Deque, Dict


@dataclass
class _RewardBucket:
    second: int
    total: float


class RollingReward:
    """Tracks per-player rewards aggregated by second within a rolling window."""

    def __init__(self, window_seconds: float) -> None:
        if window_seconds < 0:
            raise ValueError("window_seconds must be non-negative")
        self._window = float(window_seconds)
        self._buckets: Dict[int, Deque[_RewardBucket]] = defaultdict(deque)
        self._current: Dict[int, _RewardBucket] = {}
        self._sums: Dict[int, float] = defaultdict(float)

    def record(self, player_identifier: int, timestamp: float, reward: float) -> None:
        if math.isclose(reward, 0.0):
            return
        second = int(timestamp)
        current_bucket = self._current.get(player_identifier)

        if current_bucket is None:
            self._current[player_identifier] = _RewardBucket(second=second, total=reward)
            return

        if second == current_bucket.second:
            current_bucket.total += reward
            return

        if second > current_bucket.second:
            self._commit(player_identifier, current_bucket)
            self._current[player_identifier] = _RewardBucket(second=second, total=reward)
        else:
            # Out-of-order timestamps are unexpected but handled defensively.
            self._commit(player_identifier, current_bucket)
            self._insert_historical(player_identifier, second, reward)
            self._purge(player_identifier, timestamp)
            return

        self._purge(player_identifier, timestamp)

    def total(self, player_identifier: int, current_time: float) -> float:
        self._finalize_if_needed(player_identifier, current_time)
        self._purge(player_identifier, current_time)
        return self._sums.get(player_identifier, 0.0)

    def totals(self, current_time: float) -> Dict[int, float]:
        snapshot: Dict[int, float] = {}
        for identifier in list(self._buckets.keys()):
            total = self.total(identifier, current_time)
            if not math.isclose(total, 0.0):
                snapshot[identifier] = total
        # Also consider identifiers that only have a pending current bucket.
        for identifier, bucket in list(self._current.items()):
            if identifier in snapshot:
                continue
            self._finalize_if_needed(identifier, current_time)
            self._purge(identifier, current_time)
            total = self._sums.get(identifier, 0.0)
            if not math.isclose(total, 0.0):
                snapshot[identifier] = total
        return snapshot

    def reset(self) -> None:
        self._buckets.clear()
        self._current.clear()
        self._sums.clear()

    def _commit(self, player_identifier: int, bucket: _RewardBucket) -> None:
        if math.isclose(bucket.total, 0.0):
            self._current.pop(player_identifier, None)
            return
        self._buckets[player_identifier].append(bucket)
        self._sums[player_identifier] += bucket.total
        self._current.pop(player_identifier, None)

    def _insert_historical(self, player_identifier: int, second: int, reward: float) -> None:
        buckets = self._buckets[player_identifier]
        for index, existing in enumerate(buckets):
            if existing.second == second:
                existing.total += reward
                self._sums[player_identifier] += reward
                return
            if second < existing.second:
                buckets.insert(index, _RewardBucket(second=second, total=reward))
                self._sums[player_identifier] += reward
                return
        buckets.append(_RewardBucket(second=second, total=reward))
        self._sums[player_identifier] += reward

    def _finalize_if_needed(self, player_identifier: int, current_time: float) -> None:
        bucket = self._current.get(player_identifier)
        if bucket is None:
            return
        if int(current_time) > bucket.second:
            self._commit(player_identifier, bucket)

    def _purge(self, player_identifier: int, current_time: float) -> None:
        if self._window == 0.0:
            self._buckets[player_identifier].clear()
            self._sums[player_identifier] = 0.0
            self._current.pop(player_identifier, None)
            return
        cutoff = current_time - self._window
        buckets = self._buckets[player_identifier]
        while buckets and buckets[0].second + 1.0 <= cutoff:
            expired = buckets.popleft()
            self._sums[player_identifier] -= expired.total
        if not buckets and player_identifier not in self._current:
            self._sums.pop(player_identifier, None)
            return
        current_sum = self._sums.get(player_identifier)
        if current_sum is not None and math.isclose(current_sum, 0.0) and not buckets:
            self._sums.pop(player_identifier, None)

