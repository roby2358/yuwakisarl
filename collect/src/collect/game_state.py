"""Pure game state management for Collect."""

from __future__ import annotations

import random
from dataclasses import dataclass, replace
from typing import Dict, Iterable, List, Tuple

from .config import FIELD_DIMENSIONS
from .types import Action, ControllerType, GridPosition, Player


PositionOccupancy = Dict[GridPosition, int]


def _random_cell(exclusions: Iterable[GridPosition]) -> GridPosition:
    blocked = set(exclusions)
    max_attempts = FIELD_DIMENSIONS.width * FIELD_DIMENSIONS.height
    for _ in range(max_attempts):
        candidate = (
            random.randint(0, FIELD_DIMENSIONS.width - 1),
            random.randint(0, FIELD_DIMENSIONS.height - 1),
        )
        if candidate not in blocked:
            return candidate
    raise RuntimeError("Failed to locate free cell for placement")


def _adjacent_positions(position: GridPosition) -> Tuple[GridPosition, ...]:
    x_pos, y_pos = position
    neighbors: List[GridPosition] = []
    for x_delta in (-1, 0, 1):
        for y_delta in (-1, 0, 1):
            if x_delta == 0 and y_delta == 0:
                continue
            neighbor = (x_pos + x_delta, y_pos + y_delta)
            if _is_within_bounds(neighbor):
                neighbors.append(neighbor)
    return tuple(neighbors)


def _move(position: GridPosition, action: Action) -> GridPosition:
    delta_x, delta_y = action.delta()
    if delta_x == 0 and delta_y == 0:
        return position
    x_pos, y_pos = position
    return (x_pos + delta_x, y_pos + delta_y)


def _is_within_bounds(position: GridPosition) -> bool:
    x_pos, y_pos = position
    if x_pos < 0 or y_pos < 0:
        return False
    if x_pos >= FIELD_DIMENSIONS.width or y_pos >= FIELD_DIMENSIONS.height:
        return False
    return True


@dataclass
class GameObjects:
    """Tracks the mutable objects on the field."""

    players: Tuple[Player, ...]
    resources: Tuple[GridPosition, ...]
    target: GridPosition

    def to_position_map(self) -> PositionOccupancy:
        occupancy: PositionOccupancy = {}
        for player in self.players:
            occupancy[player.position] = player.identifier
        return occupancy


class GameState:
    """Encapsulates pure game logic and state transitions."""

    def __init__(self, players: Iterable[Player]) -> None:
        players_list = list(players)
        if not players_list:
            raise ValueError("GameState requires at least one player")
        self._objects = self._initialise_objects(players_list)

    @property
    def players(self) -> Tuple[Player, ...]:
        return self._objects.players

    @property
    def resources(self) -> Tuple[GridPosition, ...]:
        return self._objects.resources

    @property
    def target(self) -> GridPosition:
        return self._objects.target

    def reset_round(self) -> None:
        self._objects = self._initialise_objects(self._objects.players)

    def set_player_controller(self, player_index: int, controller: ControllerType) -> None:
        if player_index < 0 or player_index >= len(self._objects.players):
            raise IndexError("Player index out of range")
        players = list(self._objects.players)
        players[player_index] = replace(players[player_index], controller=controller)
        self._objects = GameObjects(
            players=tuple(players),
            resources=self._objects.resources,
            target=self._objects.target,
        )

    def update_player(self, player_index: int, action: Action) -> None:
        if player_index < 0 or player_index >= len(self._objects.players):
            raise IndexError("Player index out of range")
        if not isinstance(action, Action):
            raise TypeError("Action must be an instance of Action enum")

        current_objects = self._objects
        player = current_objects.players[player_index]
        desired_position = _move(player.position, action)
        if desired_position == player.position:
            self._deliver_if_ready(player_index)
            return
        if not _is_within_bounds(desired_position):
            self._deliver_if_ready(player_index)
            return
        if desired_position in current_objects.to_position_map():
            self._handle_collision(player_index)
            return
        self._objects = self._apply_move(player_index, desired_position)
        self._deliver_if_ready(player_index)

    def _apply_move(self, player_index: int, position: GridPosition) -> GameObjects:
        players = list(self._objects.players)
        player = players[player_index]
        players[player_index] = player.with_position(position)
        resources = list(self._objects.resources)
        if position in resources:
            players[player_index] = players[player_index].with_resource(True)
            resources.remove(position)
        return GameObjects(players=tuple(players), resources=tuple(resources), target=self._objects.target)

    def _handle_collision(self, player_index: int) -> None:
        player = self._objects.players[player_index]
        if not player.has_resource:
            return
        players = list(self._objects.players)
        players[player_index] = player.with_resource(False)
        resources = list(self._objects.resources)
        resources.append(self._random_resource_position(tuple(players), self._objects.target, tuple(resources)))
        self._objects = GameObjects(players=tuple(players), resources=tuple(resources), target=self._objects.target)

    def _deliver_if_ready(self, player_index: int) -> None:
        player = self._objects.players[player_index]
        if not player.has_resource:
            return
        if self._objects.target not in _adjacent_positions(player.position):
            return
        players = list(self._objects.players)
        players[player_index] = player.with_resource(False).with_score(player.score + 1)
        resources = list(self._objects.resources)
        resources.append(self._random_resource_position(tuple(players), self._objects.target, tuple(resources)))
        self._objects = GameObjects(players=tuple(players), resources=tuple(resources), target=self._objects.target)

    def _initialise_objects(self, players: Iterable[Player]) -> GameObjects:
        placements: List[Player] = []
        occupied: List[GridPosition] = []
        for player in players:
            position = self._random_cell(tuple(occupied))
            occupied.append(position)
            placements.append(replace(player, position=position, has_resource=False, score=0))
        base_players = tuple(placements)
        target_position = self._random_cell(tuple(occupied))
        resources = self._initialise_resources(base_players, target_position)
        return GameObjects(players=base_players, resources=resources, target=target_position)

    def _random_cell(self, exclusions: Iterable[GridPosition]) -> GridPosition:
        return _random_cell(exclusions)

    def _initialise_resources(self, players: Tuple[Player, ...], target: GridPosition) -> Tuple[GridPosition, ...]:
        from .config import RESOURCE_COUNT

        resources: List[GridPosition] = []
        for _ in range(RESOURCE_COUNT):
            resources.append(self._random_resource_position(players, target, tuple(resources)))
        return tuple(resources)

    def _random_resource_position(
        self,
        players: Tuple[Player, ...],
        target: GridPosition,
        existing_resources: Tuple[GridPosition, ...],
    ) -> GridPosition:
        occupied = [player.position for player in players]
        occupied.append(target)
        occupied.extend(existing_resources)
        resource_position = _random_cell(occupied)
        return resource_position

