"""Main game loop for Collect."""

from __future__ import annotations

import time
from typing import Dict, Optional, Tuple

import pygame

from .ai_controller import AIController
from .config import (
    CELL_SIZE_PX,
    DEFAULT_PLAYER_COUNT,
    FIELD_DIMENSIONS,
    FRAME_RATE,
    ROUND_BREAK_SECONDS,
    ROUND_SECONDS,
)
from .game_state import GameState
from .human_controller import HumanController
from .renderer import Renderer
from .types import Action, ControllerType, Observation, Player


class Game:
    """Encapsulates the Collect game runtime."""

    def __init__(self, player_count: int = DEFAULT_PLAYER_COUNT) -> None:
        pygame.init()
        pygame.display.set_caption("Collect")
        width = FIELD_DIMENSIONS.width * CELL_SIZE_PX
        height = FIELD_DIMENSIONS.height * CELL_SIZE_PX
        self._surface = pygame.display.set_mode((width, height))
        self._font = pygame.font.SysFont("Consolas", 16)
        self._renderer = Renderer(self._surface, self._font)
        self._clock = pygame.time.Clock()
        self._human_controller = HumanController()
        self._human_player_identifier: int | None = None
        self._escape_stage = 0
        players = self._build_players(player_count)
        self._state = GameState(players)
        self._ai_controllers: Dict[int, AIController] = {
            player.identifier: AIController(player.identifier)
            for player in self._state.players
        }
        self._running = True

    def run(self) -> None:
        while self._running:
            self._escape_stage = 0
            round_end_time = time.time() + ROUND_SECONDS
            round_active = True
            paused = False
            while round_active and self._running:
                elapsed = round_end_time - time.time()
                if elapsed <= 0:
                    round_active = False
                    break
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self._running = False
                        round_active = False
                        break
                    if event.type == pygame.KEYDOWN:
                        round_active, paused = self._handle_keydown(event.key, round_active, paused)
                        if not round_active or not self._running:
                            break
                if not round_active or not self._running:
                    break
                if paused:
                    self._renderer.draw(
                        self._state.players,
                        self._state.resources,
                        self._state.monster,
                        self._state.target,
                        elapsed,
                        paused,
                    )
                    self._clock.tick(FRAME_RATE)
                    continue
                self._tick_players()
                self._renderer.draw(
                    self._state.players,
                    self._state.resources,
                    self._state.monster,
                    self._state.target,
                    elapsed,
                    paused,
                )
                self._clock.tick(FRAME_RATE)
            if not self._running:
                break
            self._round_break()
            self._state.reset_round()

        pygame.quit()

    def _handle_keydown(self, key: int, round_active: bool, paused: bool) -> Tuple[bool, bool]:
        if key == pygame.K_SPACE:
            return round_active, not paused
        if key == pygame.K_RETURN:
            self._toggle_human_control()
            return round_active, paused
        if key == pygame.K_ESCAPE:
            if self._escape_stage == 0:
                self._escape_stage = 1
                return False, paused
            self._running = False
            return False, paused
        return round_active, paused

    def _toggle_human_control(self) -> None:
        players = self._state.players
        if not players:
            return
        player_index = 0
        player = players[player_index]
        if self._human_player_identifier == player.identifier:
            self._human_player_identifier = None
            self._state.set_player_controller(player_index, ControllerType.AI)
            return
        self._human_player_identifier = player.identifier
        self._state.set_player_controller(player_index, ControllerType.HUMAN)

    def _tick_players(self) -> None:
        pressed = pygame.key.get_pressed()
        for index, player in enumerate(self._state.players):
            controller = self._ai_controllers.get(player.identifier)
            observation = Observation(
                player=player,
                players=self._state.players,
                resources=self._state.resources,
                monster=self._state.monster,
                target=self._state.target,
            )
            action = self._select_action(player, pressed, controller, observation)
            reward = self._state.update_player(index, action)
            controller = self._ai_controllers.get(player.identifier)
            if controller is not None and self._human_player_identifier != player.identifier:
                next_observation = Observation(
                    player=self._state.players[index],
                    players=self._state.players,
                    resources=self._state.resources,
                    monster=self._state.monster,
                    target=self._state.target,
                )
                controller.observe(reward, next_observation)
        self._state.advance_environment()

    def _select_action(
        self,
        player: Player,
        pressed: pygame.key.ScancodeWrapper,
        controller: Optional[AIController],
        observation: Observation,
    ) -> Action:
        if self._human_player_identifier == player.identifier:
            return self._human_controller.select_action(pressed)
        if controller is None:
            controller = AIController(player.identifier)
            self._ai_controllers[player.identifier] = controller
        return controller.select_action(observation)

    def _round_break(self) -> None:
        end_time = time.time() + ROUND_BREAK_SECONDS
        while time.time() < end_time and self._running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False
                    break
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    if self._escape_stage == 0:
                        self._escape_stage = 1
                    else:
                        self._running = False
                        break
            remaining = end_time - time.time()
            self._renderer.draw(
                self._state.players,
                self._state.resources,
                self._state.monster,
                self._state.target,
                remaining,
                paused=True,
            )
            self._clock.tick(FRAME_RATE)

    def _build_players(self, count: int) -> Tuple[Player, ...]:
        if count <= 0:
            raise ValueError("At least one player is required")
        players = []
        for identifier in range(count):
            players.append(
                Player(
                    identifier=identifier,
                    position=(0, 0),
                    controller=ControllerType.AI,
                )
            )
        return tuple(players)

