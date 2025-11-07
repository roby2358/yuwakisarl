"""Rendering utilities for Collect."""

from __future__ import annotations

import pygame

from .config import (
    BACKGROUND_COLOR,
    CELL_SIZE_PX,
    FIELD_DIMENSIONS,
    GRID_COLOR,
    PLAYER_COLOR,
    RESOURCE_COLOR,
    TARGET_COLOR,
    TEXT_COLOR,
)
from .types import Player


class Renderer:
    """Renders the current game state onto a pygame surface."""

    def __init__(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        self._surface = surface
        self._font = font
        self._grid_surface = self._build_grid_surface()

    def draw(
        self,
        players: tuple[Player, ...],
        resources: tuple[tuple[int, int], ...],
        target: tuple[int, int],
        round_seconds_remaining: float,
        paused: bool,
    ) -> None:
        self._surface.blit(self._grid_surface, (0, 0))
        for player in players:
            self._draw_player(player)
        self._draw_resources(resources)
        self._draw_target(target)
        self._draw_hud(players, round_seconds_remaining, paused)
        pygame.display.flip()

    def _build_grid_surface(self) -> pygame.Surface:
        width = FIELD_DIMENSIONS.width * CELL_SIZE_PX
        height = FIELD_DIMENSIONS.height * CELL_SIZE_PX
        grid_surface = pygame.Surface((width, height))
        grid_surface.fill(BACKGROUND_COLOR)
        for x_pos in range(0, width, CELL_SIZE_PX):
            pygame.draw.line(grid_surface, GRID_COLOR, (x_pos, 0), (x_pos, height))
        for y_pos in range(0, height, CELL_SIZE_PX):
            pygame.draw.line(grid_surface, GRID_COLOR, (0, y_pos), (width, y_pos))
        return grid_surface

    def _draw_player(self, player: Player) -> None:
        px, py = self._cell_to_pixels(player.position)
        radius = CELL_SIZE_PX // 2
        pygame.draw.circle(self._surface, PLAYER_COLOR, (px, py), radius, width=0)
        if player.has_resource:
            pygame.draw.circle(self._surface, RESOURCE_COLOR, (px, py), radius // 2, width=0)

    def _draw_resources(self, resources: tuple[tuple[int, int], ...]) -> None:
        radius = CELL_SIZE_PX // 2
        for resource in resources:
            rx, ry = self._cell_to_pixels(resource)
            pygame.draw.circle(self._surface, RESOURCE_COLOR, (rx, ry), radius, width=0)

    def _draw_target(self, target: tuple[int, int]) -> None:
        tx, ty = self._cell_to_pixels(target)
        radius = CELL_SIZE_PX // 2
        pygame.draw.circle(self._surface, TARGET_COLOR, (tx, ty), radius, width=1)

    def _draw_hud(
        self,
        players: tuple[Player, ...],
        round_seconds_remaining: float,
        paused: bool,
    ) -> None:
        hud_surface = self._font.render(
            self._hud_text(players, round_seconds_remaining, paused),
            True,
            TEXT_COLOR,
        )
        self._surface.blit(hud_surface, (10, 10))

    def _hud_text(self, players: tuple[Player, ...], seconds_remaining: float, paused: bool) -> str:
        player_scores = ", ".join(f"P{player.identifier}: {player.score}" for player in players)
        seconds = max(0, int(seconds_remaining))
        state = "paused" if paused else "running"
        return f"{state} | time {seconds}s | {player_scores}"

    def _cell_to_pixels(self, cell: tuple[int, int]) -> tuple[int, int]:
        cx, cy = cell
        x_px = cx * CELL_SIZE_PX + CELL_SIZE_PX // 2
        y_px = cy * CELL_SIZE_PX + CELL_SIZE_PX // 2
        return x_px, y_px

