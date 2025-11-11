"""Rendering utilities for Collect."""

from __future__ import annotations

try:
    import pygame
except ModuleNotFoundError:  # pragma: no cover - optional dependency guard
    pygame = None  # type: ignore[assignment]

from .config import (
    BACKGROUND_COLOR,
    CELL_SIZE_PX,
    FIELD_DIMENSIONS,
    GRID_COLOR,
    MONSTER_COLOR,
    PLAYER_COLOR,
    RESOURCE_COLOR,
    TARGET_COLOR,
    TEXT_COLOR,
)
from .types import Player


class Renderer:
    """Renders the current game state onto a pygame surface."""

    def __init__(self, surface: "pygame.Surface", font: "pygame.font.Font") -> None:  # type: ignore[name-defined]
        if pygame is None:
            raise RuntimeError("pygame is required for rendering; install pygame to draw the game")
        self._surface = surface
        self._font = font
        self._grid_surface = self._build_grid_surface()

    def draw(
        self,
        players: tuple[Player, ...],
        resources: tuple[tuple[int, int], ...],
        monster: tuple[int, int],
        target: tuple[int, int],
        round_seconds_remaining: float,
        paused: bool,
        rolling_scores: dict[int, int] | None = None,
        epsilon_percentages: dict[int, float] | None = None,
        rolling_rewards: dict[int, float] | None = None,
    ) -> None:
        self._surface.blit(self._grid_surface, (0, 0))
        for player in players:
            self._draw_player(player)
        self._draw_resources(resources)
        self._draw_target(target)
        self._draw_monster(monster)
        self._draw_hud(
            players,
            round_seconds_remaining,
            paused,
            rolling_scores,
            epsilon_percentages,
            rolling_rewards,
        )
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

    def _draw_monster(self, monster: tuple[int, int]) -> None:
        mx, my = self._cell_to_pixels(monster)
        radius = max(1, CELL_SIZE_PX // 2)
        pygame.draw.circle(self._surface, MONSTER_COLOR, (mx, my), radius, width=0)

    def _draw_hud(
        self,
        players: tuple[Player, ...],
        round_seconds_remaining: float,
        paused: bool,
        rolling_scores: dict[int, int] | None,
        epsilon_percentages: dict[int, float] | None,
        rolling_rewards: dict[int, float] | None,
    ) -> None:
        hud_text = self._hud_text(
            players,
            round_seconds_remaining,
            paused,
            rolling_scores,
            epsilon_percentages,
            rolling_rewards,
        )
        if not hud_text:
            return
        line_height = self._font.get_linesize()
        for index, line in enumerate(hud_text.splitlines()):
            hud_surface = self._font.render(line, True, TEXT_COLOR)
            self._surface.blit(hud_surface, (10, 10 + index * line_height))

    def _hud_text(
        self,
        players: tuple[Player, ...],
        seconds_remaining: float,
        paused: bool,
        rolling_scores: dict[int, int] | None,
        epsilon_percentages: dict[int, float] | None,
        rolling_rewards: dict[int, float] | None = None,
    ) -> str:
        epsilon_lookup = epsilon_percentages or {}
        rolling_lookup = rolling_scores or {}
        reward_lookup = rolling_rewards or {}
        player_lines = [
            self._player_fragment(
                player,
                rolling_lookup.get(player.identifier),
                epsilon_lookup.get(player.identifier),
                reward_lookup.get(player.identifier),
            )
            for player in players
        ]
        seconds = max(0, int(seconds_remaining))
        lines = [f"{seconds}s"]
        lines.extend(player_lines)
        return "\n".join(lines)

    def _player_fragment(
        self,
        player: Player,
        rolling_total: int | None,
        epsilon_percent: float | None,
        rolling_reward: float | None,
    ) -> str:
        base = f"{player.identifier}: {player.score}"
        if rolling_total is not None:
            base = f"{player.identifier}: {rolling_total}/{player.score}"
        fragments = [base]
        if epsilon_percent is not None:
            fragments.append(f"{epsilon_percent:.1f}%")
        if rolling_reward is not None:
            fragments.append(f"rr:{rolling_reward:+.2f}")
        return " ".join(fragments)

    def _cell_to_pixels(self, cell: tuple[int, int]) -> tuple[int, int]:
        cx, cy = cell
        x_px = cx * CELL_SIZE_PX + CELL_SIZE_PX // 2
        y_px = cy * CELL_SIZE_PX + CELL_SIZE_PX // 2
        return x_px, y_px

