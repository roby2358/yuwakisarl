"""Tests for the pure game logic in GameState."""

from __future__ import annotations

from typing import Iterator, Tuple

import pytest

from collect.game_state import GameState
from collect.types import Action, ControllerType, Player


def deterministic_cells(*cells: Tuple[int, int]) -> Iterator[Tuple[int, int]]:
    for cell in cells:
        yield cell
    while True:
        yield cells[-1]


def test_player_collects_resource(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("collect.config.RESOURCE_COUNT", 1, raising=False)
    cells = deterministic_cells((1, 1), (5, 5), (2, 1), (3, 3))

    def next_cell(exclusions: tuple[Tuple[int, int], ...]) -> Tuple[int, int]:
        return next(cells)

    monkeypatch.setattr("collect.game_state._random_cell", next_cell)
    player = Player(identifier=0, position=(0, 0), controller=ControllerType.AI)
    state = GameState([player])

    state.update_player(0, Action.MOVE_RIGHT)
    assert state.players[0].position == (2, 1)
    assert state.players[0].has_resource is True
    assert len(state.resources) == 0


def test_player_delivers_resource(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("collect.config.RESOURCE_COUNT", 1, raising=False)
    cells = deterministic_cells(
        (1, 1),  # player start
        (5, 5),  # target
        (2, 1),  # resource initial
        (10, 10),  # resource after pickup
        (15, 15),  # resource after delivery
    )

    def next_cell(exclusions: tuple[Tuple[int, int], ...]) -> Tuple[int, int]:
        return next(cells)

    monkeypatch.setattr("collect.game_state._random_cell", next_cell)
    player = Player(identifier=0, position=(0, 0), controller=ControllerType.AI)
    state = GameState([player])

    state.update_player(0, Action.MOVE_RIGHT)
    assert state.players[0].has_resource is True

    moves = [
        Action.MOVE_RIGHT,
        Action.MOVE_RIGHT,
        Action.MOVE_DOWN,
        Action.MOVE_DOWN,
        Action.MOVE_DOWN,
        Action.MOVE_DOWN,
    ]
    for action in moves:
        state.update_player(0, action)
    assert state.players[0].has_resource is False
    assert state.players[0].score == 1
    assert len(state.resources) == 1


def test_collision_drops_resource(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("collect.config.RESOURCE_COUNT", 1, raising=False)
    cells = deterministic_cells(
        (1, 1),  # player 0 start
        (1, 2),  # player 1 start
        (5, 5),  # target
        (2, 1),  # resource initial
        (10, 10),  # resource after pickup
        (7, 7),  # resource after collision drop
    )

    def next_cell(exclusions: tuple[Tuple[int, int], ...]) -> Tuple[int, int]:
        return next(cells)

    monkeypatch.setattr("collect.game_state._random_cell", next_cell)
    player0 = Player(identifier=0, position=(0, 0), controller=ControllerType.AI)
    player1 = Player(identifier=1, position=(0, 0), controller=ControllerType.AI)
    state = GameState([player0, player1])

    state.update_player(0, Action.MOVE_RIGHT)
    assert state.players[0].has_resource is True
    assert len(state.resources) == 0

    state.update_player(0, Action.MOVE_DOWN)
    assert state.players[0].position == (2, 2)
    state.update_player(0, Action.MOVE_LEFT)
    assert state.players[0].has_resource is False
    assert len(state.resources) == 1

