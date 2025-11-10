"""Tests for the pure game logic in GameState."""

from __future__ import annotations

from typing import Iterator, Tuple

import pytest

from collect.config import FIELD_DIMENSIONS, SHAPING_REWARD_MAX, SHAPING_REWARD_MIN
from collect.game_state import GameObjects, GameState
from collect.types import Action, ControllerType, Player


def deterministic_cells(*cells: Tuple[int, int]) -> Iterator[Tuple[int, int]]:
    for cell in cells:
        yield cell
    while True:
        yield cells[-1]


@pytest.fixture(autouse=True)
def disable_monster_movement(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("collect.game_state.random.random", lambda: 1.0)


def test_player_collects_resource(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("collect.config.RESOURCE_COUNT", 1, raising=False)
    cells = deterministic_cells(
        (40, 40),  # player start
        (60, 60),  # monster position
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
        (150, 150),  # monster position
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
        (5, 5),  # monster position
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
        (8, 8),  # monster position
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
        (40, 40),  # monster position
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

    new_resource = state._random_resource_position(state.players, state.target, state.resources, state.monster)
    assert new_resource not in state.resources
    assert any(state.resources[0] in exclusions for exclusions in observed_exclusions)


def test_player_carrying_cannot_collect_second_resource(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("collect.config.RESOURCE_COUNT", 2, raising=False)
    cells = deterministic_cells(
        (10, 10),  # player position
        (20, 20),  # monster position
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


def test_monster_moves_toward_nearest_carrier(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("collect.game_state.random.random", lambda: 0.0)
    carrier = Player(identifier=0, position=(5, 5), controller=ControllerType.AI).with_resource(True)
    other = Player(identifier=1, position=(10, 10), controller=ControllerType.AI)
    state = GameState([carrier, other])
    state._objects = GameObjects(
        players=(carrier, other),
        resources=(),
        target=(20, 20),
        monster=(0, 0),
    )

    state.update_player(0, Action.STAY)
    state.advance_environment()

    assert state.monster == (1, 1)


def test_monster_steals_resource_when_colliding(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("collect.config.RESOURCE_COUNT", 0, raising=False)
    monkeypatch.setattr("collect.game_state.random.random", lambda: 0.0)
    monkeypatch.setattr(
        "collect.game_state.GameState._random_resource_position",
        lambda self, *_: (6, 6),
        raising=False,
    )
    carrier = Player(identifier=0, position=(4, 4), controller=ControllerType.AI).with_resource(True)
    state = GameState([carrier])
    state._objects = GameObjects(
        players=(carrier,),
        resources=(),
        target=(20, 20),
        monster=(3, 3),
    )

    state.update_player(0, Action.STAY)
    state.advance_environment()

    assert state.players[0].has_resource is False
    assert state.monster == (4, 4)
    assert len(state.resources) == 1
    assert state.resources[0] == (6, 6)


def test_monster_moves_only_when_random_below_threshold(monkeypatch: pytest.MonkeyPatch) -> None:
    def build_state() -> GameState:
        carrier = Player(identifier=0, position=(4, 4), controller=ControllerType.AI).with_resource(True)
        state = GameState([carrier])
        state._objects = GameObjects(
            players=(carrier,),
            resources=(),
            target=(10, 10),
            monster=(0, 0),
        )
        return state

    monkeypatch.setattr("collect.game_state.random.random", lambda: 0.29)
    moving_state = build_state()
    moving_state.update_player(0, Action.STAY)
    moving_state.advance_environment()
    assert moving_state.monster == (1, 1)

    monkeypatch.setattr("collect.game_state.random.random", lambda: 0.3)
    stationary_state = build_state()
    stationary_state.update_player(0, Action.STAY)
    stationary_state.advance_environment()
    assert stationary_state.monster == (0, 0)


def test_monster_reward_positive_when_distance_increases() -> None:
    player = Player(identifier=0, position=(5, 5), controller=ControllerType.AI)
    state = GameState([player])
    configured_player = player.with_position((5, 5))
    state._objects = GameObjects(
        players=(configured_player,),
        resources=(),
        target=(10, 10),
        monster=(5, 5),
    )

    reward = state.update_player(0, Action.MOVE_RIGHT)

    assert reward == pytest.approx(0.05)


def test_monster_reward_negative_when_distance_decreases() -> None:
    player = Player(identifier=0, position=(5, 5), controller=ControllerType.AI)
    state = GameState([player])
    configured_player = player.with_position((5, 5))
    state._objects = GameObjects(
        players=(configured_player,),
        resources=(),
        target=(10, 10),
        monster=(7, 5),
    )

    reward = state.update_player(0, Action.MOVE_RIGHT)

    assert reward == pytest.approx(-0.05)


def _expected_magnitude(distance: int) -> float:
    max_distance = FIELD_DIMENSIONS.width + FIELD_DIMENSIONS.height - 2
    return SHAPING_REWARD_MIN + (SHAPING_REWARD_MAX - SHAPING_REWARD_MIN) * (distance / max_distance)


def test_shaping_reward_scales_positive_with_distance() -> None:
    player = Player(identifier=0, position=(0, 0), controller=ControllerType.AI).with_resource(True)
    state = GameState([player])
    configured_player = player.with_position((10, 10))
    state._objects = GameObjects(
        players=(configured_player,),
        resources=(),
        target=(13, 10),
        monster=(0, 0),
    )

    before_distance = 4
    reward = state._shaping_reward(player_index=0, before_distance=before_distance)

    after_distance = state._distance_to_goal(configured_player, state.resources, state.target)
    assert after_distance is not None

    assert after_distance < before_distance
    assert reward == pytest.approx(_expected_magnitude(after_distance))


def test_shaping_reward_scales_negative_with_distance() -> None:
    player = Player(identifier=0, position=(0, 0), controller=ControllerType.AI).with_resource(True)
    state = GameState([player])
    configured_player = player.with_position((20, 20))
    state._objects = GameObjects(
        players=(configured_player,),
        resources=(),
        target=(10, 20),
        monster=(0, 0),
    )

    before_distance = 9
    reward = state._shaping_reward(player_index=0, before_distance=before_distance)

    after_distance = state._distance_to_goal(configured_player, state.resources, state.target)
    assert after_distance is not None

    assert reward == pytest.approx(-_expected_magnitude(after_distance))


def test_shaping_reward_uses_minimum_when_distance_zero() -> None:
    player = Player(identifier=0, position=(0, 0), controller=ControllerType.AI).with_resource(True)
    state = GameState([player])
    configured_player = player.with_position((50, 50))
    state._objects = GameObjects(
        players=(configured_player,),
        resources=(),
        target=(50, 50),
        monster=(0, 0),
    )

    reward = state._shaping_reward(player_index=0, before_distance=1)

    assert reward == pytest.approx(_expected_magnitude(0))


def test_shaping_reward_returns_zero_when_before_distance_unknown() -> None:
    player = Player(identifier=0, position=(0, 0), controller=ControllerType.AI)
    state = GameState([player])

    reward = state._shaping_reward(player_index=0, before_distance=None)

    assert reward == 0.0