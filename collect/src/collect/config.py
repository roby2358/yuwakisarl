"""Constant values for the Collect game."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FieldDimensions:
    """Represents the playing field dimensions."""

    width: int
    height: int


FIELD_DIMENSIONS = FieldDimensions(width=200, height=200)
CELL_SIZE_PX = 4
FRAME_RATE = 30
ROUND_SECONDS = 24 * 60 * 60
ROUND_BREAK_SECONDS = 10
BACKGROUND_COLOR = (10, 10, 10)
GRID_COLOR = (30, 30, 30)
PLAYER_COLOR = (240, 240, 240)
RESOURCE_COLOR = (255, 221, 0)
TARGET_COLOR = (200, 200, 200)
TEXT_COLOR = (200, 200, 200)
DEFAULT_PLAYER_COUNT = 6
RESOURCE_COUNT = 15
SHAPING_REWARD = 0.1
SHAPING_REWARD_CLOSE = 0.3
SHAPING_REWARD_CLOSE_DISTANCE = 3
COLLISION_PENALTY = 0.0

