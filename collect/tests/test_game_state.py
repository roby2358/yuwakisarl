"""Tests for the pure game logic in GameState."""

from __future__ import annotations

from typing import Iterator, Tuple

import pytest

from collect.config import SHAPING_REWARD, SHAPING_REWARD_CLOSE
from collect.game_state import GameObjects, GameState
from collect.types import Action, ControllerType, Player


def deterministic_cells(*cells: Tuple[int, int]) -> Iterator[Tuple[int, int]]:
    for cell in cells:
        yield cell
    while True:
        yield cells[-1]


def test_player_collects_resource(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("collect.config.RESOURCE_COUNT", 1, raising=False)
    cells = deterministic_cells(
        (40, 40),  # player start
        (41, 40),  # resource position
    )

    def next_cell(exclusions: tuple[Tuple[int, int], ...]) -> Tuple[int, int]:
        while True:
            candidate = next(cells)
            if candidate in exclusions:
                continue
            return candidate

    monkeypatch.setattr("collect.game_state._random_cell", next_cell)
    player = Player(identifier=0, position=(0, 0), controller=ControllerType.AI)
    state = GameState([player])

    resource = state.resources[0]
    action = Action.from_delta(resource[0] - state.players[0].position[0], resource[1] - state.players[0].position[1])
    state.update_player(0, action)
    assert state.players[0].has_resource is True
    assert len(state.resources) == 0


def test_player_delivers_resource(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("collect.config.RESOURCE_COUNT", 1, raising=False)
    cells = deterministic_cells(
        (101, 100),  # player start near target
        (100, 100),  # blocked target position (should be skipped)
        (100, 99),  # blocked adjacent position (should be skipped)
        (101, 99),  # blocked adjacent position (should be skipped)
        (102, 100),  # resource initial (allowed)
        (110, 110),  # resource after pickup
        (120, 120),  # resource after delivery
    )

    def next_cell(exclusions: tuple[Tuple[int, int], ...]) -> Tuple[int, int]:
        while True:
            candidate = next(cells)
            if candidate in exclusions:
                continue
            return candidate

    monkeypatch.setattr("collect.game_state._random_cell", next_cell)
    player = Player(identifier=0, position=(0, 0), controller=ControllerType.AI)
    state = GameState([player])

    state.update_player(0, Action.MOVE_RIGHT)
    assert state.players[0].position == (102, 100)
    assert state.players[0].has_resource is True
    state.update_player(0, Action.MOVE_LEFT)
    assert state.players[0].position == (101, 100)
    assert state.players[0].has_resource is False
    assert state.target == (100, 100)
    assert state.players[0].score == 1
    assert len(state.resources) == 1


def test_collision_drops_resource(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("collect.config.RESOURCE_COUNT", 1, raising=False)
    cells = deterministic_cells(
        (1, 1),  # player 0 start
        (1, 2),  # player 1 start
        (2, 1),  # resource initial
        (10, 10),  # resource after pickup
        (7, 7),  # resource after collision drop
    )

    def next_cell(exclusions: tuple[Tuple[int, int], ...]) -> Tuple[int, int]:
        while True:
            candidate = next(cells)
            if candidate in exclusions:
                continue
            return candidate

    monkeypatch.setattr("collect.game_state._random_cell", next_cell)
    player0 = Player(identifier=0, position=(0, 0), controller=ControllerType.AI)
    player1 = Player(identifier=1, position=(0, 0), controller=ControllerType.AI)
    state = GameState([player0, player1])

    state.update_player(0, Action.MOVE_RIGHT)
    assert state.players[0].has_resource is True
    assert state.target == (100, 100)
    assert len(state.resources) == 0

    state.update_player(0, Action.MOVE_DOWN)
    assert state.players[0].position == (2, 2)
    state.update_player(0, Action.MOVE_LEFT)
    assert state.players[0].has_resource is False
    assert len(state.resources) == 1


def test_collision_penalty_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("collect.config.RESOURCE_COUNT", 0, raising=False)
    cells = deterministic_cells(
        (5, 5),  # player 0 start
        (5, 6),  # player 1 start
    )

    def next_cell(exclusions: tuple[Tuple[int, int], ...]) -> Tuple[int, int]:
        while True:
            candidate = next(cells)
            if candidate in exclusions:
                continue
            return candidate

    monkeypatch.setattr("collect.game_state._random_cell", next_cell)
    player0 = Player(identifier=0, position=(0, 0), controller=ControllerType.AI)
    player1 = Player(identifier=1, position=(0, 0), controller=ControllerType.AI)
    state = GameState([player0, player1])

    reward = state.update_player(0, Action.MOVE_DOWN)

    assert reward == 0.0
    assert state.players[0].position == (5, 5)
    assert state.players[0].has_resource is False


def test_distance_to_goal_with_resource_targets_center(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("collect.game_state._random_cell", lambda exclusions: (50, 50))
    player = Player(identifier=0, position=(0, 0), controller=ControllerType.AI)
    state = GameState([player])

    carrying_player = Player(identifier=0, position=(60, 90), controller=ControllerType.AI, has_resource=True)
    distance = state._distance_to_goal(carrying_player, tuple(), state.target)

    assert distance == abs(carrying_player.position[0] - state.target[0]) + abs(carrying_player.position[1] - state.target[1])


def test_resources_never_spawn_in_target_zone(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("collect.config.RESOURCE_COUNT", 2, raising=False)
    candidate_pool = [
        (100, 100),  # target, should be skipped
        (100, 99),  # adjacent, should be skipped
        (100, 101),  # adjacent, should be skipped
        (99, 100),  # adjacent, should be skipped
        (101, 100),  # adjacent, should be skipped
        (10, 10),
        (12, 12),
        (14, 14),
        (16, 16),
    ]
    index = 0

    def next_cell(exclusions: tuple[Tuple[int, int], ...]) -> Tuple[int, int]:
        nonlocal index
        checked = 0
        pool_length = len(candidate_pool)
        while checked < pool_length:
            candidate = candidate_pool[index % pool_length]
            index += 1
            checked += 1
            if candidate in exclusions:
                continue
            return candidate
        raise AssertionError("Exhausted deterministic candidates while searching for free cell")

    monkeypatch.setattr("collect.game_state._random_cell", next_cell)
    player = Player(identifier=0, position=(0, 0), controller=ControllerType.AI)
    state = GameState([player])

    forbidden = {
        (100, 100),
        (100, 99),
        (100, 101),
        (99, 100),
        (101, 100),
    }
    assert all(resource not in forbidden for resource in state.resources)


def test_resources_do_not_overlap(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("collect.config.RESOURCE_COUNT", 2, raising=False)
    placement_sequence = [
        (30, 30),  # player position
        (60, 60),  # first resource
        (60, 60),  # duplicate attempt that should be excluded
        (70, 70),  # second resource
        (80, 80),  # respawn after collection
    ]
    index = 0
    observed_exclusions: list[set[Tuple[int, int]]] = []

    def next_cell(exclusions: tuple[Tuple[int, int], ...]) -> Tuple[int, int]:
        nonlocal index
        observed_exclusions.append(set(exclusions))
        tested = 0
        while tested < len(placement_sequence):
            candidate = placement_sequence[index % len(placement_sequence)]
            index += 1
            tested += 1
            if candidate in exclusions:
                continue
            return candidate
        raise AssertionError("Exhausted deterministic candidates while searching for free cell")

    monkeypatch.setattr("collect.game_state._random_cell", next_cell)
    player = Player(identifier=0, position=(0, 0), controller=ControllerType.AI)
    state = GameState([player])

    assert len(state.resources) == 2
    assert len(set(state.resources)) == len(state.resources)

    new_resource = state._random_resource_position(state.players, state.target, state.resources)
    assert new_resource not in state.resources
    assert any(state.resources[0] in exclusions for exclusions in observed_exclusions)


def test_player_carrying_cannot_collect_second_resource(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("collect.config.RESOURCE_COUNT", 2, raising=False)
    cells = deterministic_cells(
        (10, 10),  # player position
        (11, 10),  # first resource
        (12, 10),  # second resource
    )

    def next_cell(exclusions: tuple[Tuple[int, int], ...]) -> Tuple[int, int]:
        while True:
            candidate = next(cells)
            if candidate in exclusions:
                continue
            return candidate

    monkeypatch.setattr("collect.game_state._random_cell", next_cell)
    player = Player(identifier=0, position=(0, 0), controller=ControllerType.AI)
    state = GameState([player])

    assert state.players[0].position == (10, 10)
    assert set(state.resources) == {(11, 10), (12, 10)}

    state.update_player(0, Action.MOVE_RIGHT)
    assert state.players[0].has_resource is True
    assert state.players[0].position == (11, 10)

    state.update_player(0, Action.MOVE_RIGHT)

    assert state.players[0].position == (11, 10)
    assert state.players[0].has_resource is True
    assert set(state.resources) == {(12, 10)}


def test_shaping_reward_increases_when_close_positive() -> None:
    player = Player(identifier=0, position=(0, 0), controller=ControllerType.AI)
    state = GameState([player])
    close_player = player.with_position((0, 0))
    close_resources = ((1, 2),)
    state._objects = GameObjects(players=(close_player,), resources=close_resources, target=(10, 10))

    reward = state._shaping_reward(player_index=0, before_distance=4)

    assert reward == SHAPING_REWARD_CLOSE


def test_shaping_reward_increases_when_close_negative() -> None:
    player = Player(identifier=0, position=(0, 0), controller=ControllerType.AI)
    state = GameState([player])
    far_player = player.with_position((0, 0))
    far_resources = ((5, 0),)
    state._objects = GameObjects(players=(far_player,), resources=far_resources, target=(10, 10))

    reward = state._shaping_reward(player_index=0, before_distance=2)

    assert reward == -SHAPING_REWARD_CLOSE


def test_shaping_reward_uses_default_magnitude_when_far() -> None:
    player = Player(identifier=0, position=(0, 0), controller=ControllerType.AI)
    state = GameState([player])
    far_player = player.with_position((0, 0))
    far_resources = ((20, 0),)
    state._objects = GameObjects(players=(far_player,), resources=far_resources, target=(10, 10))

    reward = state._shaping_reward(player_index=0, before_distance=12)

    assert reward == -SHAPING_REWARD