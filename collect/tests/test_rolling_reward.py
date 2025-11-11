from __future__ import annotations

import pytest

from collect.rolling_reward import RollingReward


def test_rolling_reward_commits_on_second_boundary() -> None:
    tracker = RollingReward(window_seconds=300.0)

    tracker.record(player_identifier=1, timestamp=10.2, reward=1.5)
    tracker.record(player_identifier=1, timestamp=10.8, reward=0.5)

    assert tracker.total(1, current_time=10.9) == pytest.approx(0.0)
    assert tracker.total(1, current_time=11.1) == pytest.approx(2.0)


def test_rolling_reward_purges_outside_window() -> None:
    tracker = RollingReward(window_seconds=3.0)

    tracker.record(player_identifier=2, timestamp=100.1, reward=1.0)
    tracker.record(player_identifier=2, timestamp=101.4, reward=2.0)
    assert tracker.total(2, current_time=103.5) == pytest.approx(3.0)

    tracker.record(player_identifier=2, timestamp=105.2, reward=-0.5)
    assert tracker.total(2, current_time=105.3) == pytest.approx(0.0)
    assert tracker.total(2, current_time=106.2) == pytest.approx(-0.5)
    assert tracker.total(2, current_time=110.2) == pytest.approx(0.0)


def test_rolling_reward_handles_out_of_order_timestamps() -> None:
    tracker = RollingReward(window_seconds=10.0)

    tracker.record(player_identifier=3, timestamp=50.5, reward=1.0)
    tracker.record(player_identifier=3, timestamp=52.2, reward=2.0)
    tracker.record(player_identifier=3, timestamp=51.6, reward=0.5)

    assert tracker.total(3, current_time=53.1) == pytest.approx(3.5)

