"""Pure game state management for Collect."""

from __future__ import annotations

import random
import math
from dataclasses import dataclass, replace
from typing import Dict, Iterable, List, Optional, Tuple

from .config import (
    COLLISION_PENALTY,
    FIELD_DIMENSIONS,
    MONSTER_REWARD_MAX,
    MONSTER_REWARD_SCALE,
    SHAPING_REWARD_MAX,
    SHAPING_REWARD_MIN,
)
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


def _target_exclusion_zone(target: GridPosition) -> Tuple[GridPosition, ...]:
    zone = {target}
    zone.update(_adjacent_positions(target))
    return tuple(zone)


def _move(position: GridPosition, action: Action) -> GridPosition:
    delta_x, delta_y = action.delta()
    if delta_x == 0 and delta_y == 0:
        return position
    x_pos, y_pos = position
    return (x_pos + delta_x, y_pos + delta_y)


def _euclidean_distance(a: GridPosition, b: GridPosition) -> float:
    delta_x = a[0] - b[0]
    delta_y = a[1] - b[1]
    return math.hypot(delta_x, delta_y)


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
    monster: GridPosition

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

    @property
    def monster(self) -> GridPosition:
        return self._objects.monster

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
            monster=self._objects.monster,
        )

    def update_player(self, player_index: int, action: Action) -> float:
        if player_index < 0 or player_index >= len(self._objects.players):
            raise IndexError("Player index out of range")
        if not isinstance(action, Action):
            raise TypeError("Action must be an instance of Action enum")

        current_objects = self._objects
        player = current_objects.players[player_index]
        before_score = player.score
        before_distance = self._distance_to_goal(player, current_objects.resources, current_objects.target)
        monster_position_before = current_objects.monster
        before_monster_distance = self._distance_to_monster(player, monster_position_before)
        desired_position = _move(player.position, action)
        penalty = 0.0
        if desired_position != player.position:
            if not _is_within_bounds(desired_position):
                penalty += 0.0
            else:
                if player.has_resource and desired_position in current_objects.resources:
                    desired_position = player.position
                else:
                    occupancy = current_objects.to_position_map()
                    if desired_position in occupancy:
                        self._handle_collision(player_index)
                        penalty += COLLISION_PENALTY
                    else:
                        self._objects = self._apply_move(player_index, desired_position)
        self._deliver_if_ready(player_index)
        shaping = self._shaping_reward(player_index, before_distance)
        after_score = self._objects.players[player_index].score
        player_after_move = self._objects.players[player_index]
        after_monster_distance = self._distance_to_monster(player_after_move, monster_position_before)
        monster_reward = self._monster_distance_reward(before_monster_distance, after_monster_distance)
        return shaping + penalty + float(after_score - before_score) + monster_reward

    def _apply_move(self, player_index: int, position: GridPosition) -> GameObjects:
        players = list(self._objects.players)
        player = players[player_index]
        players[player_index] = player.with_position(position)
        resources = list(self._objects.resources)
        if position in resources:
            players[player_index] = players[player_index].with_resource(True)
            resources.remove(position)
        return GameObjects(
            players=tuple(players),
            resources=tuple(resources),
            target=self._objects.target,
            monster=self._objects.monster,
        )

    def _handle_collision(self, player_index: int) -> None:
        player = self._objects.players[player_index]
        if not player.has_resource:
            return
        players = list(self._objects.players)
        players[player_index] = player.with_resource(False)
        resources = list(self._objects.resources)
        resources.append(
            self._random_resource_position(
                tuple(players),
                self._objects.target,
                tuple(resources),
                self._objects.monster,
            )
        )
        self._objects = GameObjects(
            players=tuple(players),
            resources=tuple(resources),
            target=self._objects.target,
            monster=self._objects.monster,
        )

    def _deliver_if_ready(self, player_index: int) -> None:
        player = self._objects.players[player_index]
        if not player.has_resource:
            return
        if player.position != self._objects.target:
            return
        players = list(self._objects.players)
        players[player_index] = player.with_resource(False).with_score(player.score + 1)
        resources = list(self._objects.resources)
        resources.append(
            self._random_resource_position(
                tuple(players),
                self._objects.target,
                tuple(resources),
                self._objects.monster,
            )
        )
        self._objects = GameObjects(
            players=tuple(players),
            resources=tuple(resources),
            target=self._objects.target,
            monster=self._objects.monster,
        )

    def _initialise_objects(self, players: Iterable[Player]) -> GameObjects:
        placements: List[Player] = []
        occupied: List[GridPosition] = []
        for player in players:
            position = self._random_cell(tuple(occupied))
            occupied.append(position)
            placements.append(replace(player, position=position, has_resource=False, score=0))
        base_players = tuple(placements)
        target_x = FIELD_DIMENSIONS.width // 2
        target_y = FIELD_DIMENSIONS.height // 2
        target_position = (target_x, target_y)
        monster_position = self._initialise_monster(base_players, target_position)
        resources = self._initialise_resources(base_players, target_position, monster_position)
        return GameObjects(
            players=base_players,
            resources=resources,
            target=target_position,
            monster=monster_position,
        )

    def _random_cell(self, exclusions: Iterable[GridPosition]) -> GridPosition:
        return _random_cell(exclusions)

    def _initialise_monster(self, players: Tuple[Player, ...], target: GridPosition) -> GridPosition:
        return self._random_monster_position(players, target)

    def _random_monster_position(self, players: Tuple[Player, ...], target: GridPosition) -> GridPosition:
        blocked: set[GridPosition] = {player.position for player in players}
        blocked.update(_target_exclusion_zone(target))
        return _random_cell(tuple(blocked))

    def _initialise_resources(
        self,
        players: Tuple[Player, ...],
        target: GridPosition,
        monster_position: GridPosition,
    ) -> Tuple[GridPosition, ...]:
        from .config import RESOURCE_COUNT

        resources: List[GridPosition] = []
        for _ in range(RESOURCE_COUNT):
            resources.append(self._random_resource_position(players, target, tuple(resources), monster_position))
        return tuple(resources)

    def _random_resource_position(
        self,
        players: Tuple[Player, ...],
        target: GridPosition,
        existing_resources: Tuple[GridPosition, ...],
        monster_position: GridPosition,
    ) -> GridPosition:
        occupied: set[GridPosition] = {player.position for player in players}
        occupied.update(_target_exclusion_zone(target))
        occupied.update(existing_resources)
        occupied.add(monster_position)
        resource_position = _random_cell(tuple(occupied))
        return resource_position

    def _distance_to_goal(
        self, player: Player, resources: Tuple[GridPosition, ...], target: GridPosition
    ) -> Optional[float]:
        if player.has_resource:
            return _euclidean_distance(player.position, target)
        if not resources:
            return None
        return min(_euclidean_distance(player.position, resource) for resource in resources)

    def _distance_to_monster(self, player: Player, monster_position: GridPosition) -> float:
        return _euclidean_distance(player.position, monster_position)

    def _shaping_reward(self, player_index: int, before_distance: Optional[float]) -> float:
        if before_distance is None:
            return 0.0
        player = self._objects.players[player_index]
        after_distance = self._distance_to_goal(player, self._objects.resources, self._objects.target)
        if after_distance is None:
            return 0.0

        max_distance = math.hypot(FIELD_DIMENSIONS.width - 1, FIELD_DIMENSIONS.height - 1)
        if max_distance <= 0.0:
            return 0.0

        def scaled_magnitude(distance: float) -> float:
            clamped_distance = max(0.0, min(distance, max_distance))
            scale = clamped_distance / max_distance
            delta = SHAPING_REWARD_MAX - SHAPING_REWARD_MIN
            return SHAPING_REWARD_MIN + (delta * scale)

        magnitude_distance = after_distance
        if after_distance < before_distance:
            return scaled_magnitude(magnitude_distance)
        return -scaled_magnitude(magnitude_distance)

    def _monster_distance_reward(
        self, before_distance: Optional[float], after_distance: Optional[float]
    ) -> float:
        if before_distance is None or after_distance is None:
            return 0.0
        if before_distance == after_distance:
            return 0.0
        delta = after_distance - before_distance
        magnitude = min(MONSTER_REWARD_MAX, abs(delta) * MONSTER_REWARD_SCALE)
        return -magnitude if delta > 0 else magnitude

    def _maybe_move_monster(self) -> None:
        carriers = [player for player in self._objects.players if player.has_resource]
        if not carriers:
            return
        if random.random() >= 0.3:
            return
        monster_position = self._objects.monster
        target_player = min(carriers, key=lambda candidate: _euclidean_distance(candidate.position, monster_position))
        step_x = self._step_towards(monster_position[0], target_player.position[0])
        step_y = self._step_towards(monster_position[1], target_player.position[1])
        next_position = (monster_position[0] + step_x, monster_position[1] + step_y)
        if not _is_within_bounds(next_position):
            next_position = monster_position
        players = list(self._objects.players)
        resources = list(self._objects.resources)
        self._steal_resource_if_present(next_position, players, resources)
        self._objects = GameObjects(
            players=tuple(players),
            resources=tuple(resources),
            target=self._objects.target,
            monster=next_position,
        )

    def _steal_resource_if_present(
        self,
        position: GridPosition,
        players: List[Player],
        resources: List[GridPosition],
    ) -> None:
        for index, candidate in enumerate(players):
            if candidate.position != position or not candidate.has_resource:
                continue
            players[index] = candidate.with_resource(False)
            new_resource = self._random_resource_position(
                tuple(players),
                self._objects.target,
                tuple(resources),
                position,
            )
            resources.append(new_resource)
            return

    def advance_environment(self) -> None:
        """Advance non-player entities such as the monster."""
        self._maybe_move_monster()

    def _step_towards(self, start: int, end: int) -> int:
        if end > start:
            return 1
        if end < start:
            return -1
        return 0

