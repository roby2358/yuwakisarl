from __future__ import annotations

from collect.rolling_score import RollingScore


def test_rolling_score_counts_events_within_window() -> None:
    tracker = RollingScore(window_seconds=300.0)
    tracker.record(player_identifier=1, timestamp=0.0)
    tracker.record(player_identifier=1, timestamp=100.0)
    tracker.record(player_identifier=1, timestamp=400.0)

    assert tracker.total(1, current_time=250.0) == 3
    assert tracker.total(1, current_time=350.0) == 2
    assert tracker.total(1, current_time=701.0) == 0


def test_rolling_score_totals_filters_zero_entries() -> None:
    tracker = RollingScore(window_seconds=10.0)
    tracker.record(player_identifier=1, timestamp=0.0)
    tracker.record(player_identifier=2, timestamp=6.0)

    snapshot_initial = tracker.totals(current_time=6.0)
    assert snapshot_initial == {1: 1, 2: 1}

    snapshot_after_window = tracker.totals(current_time=11.0)
    assert snapshot_after_window == {2: 1}

