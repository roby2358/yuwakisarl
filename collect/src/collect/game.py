"""Main game loop for Collect."""

from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

try:
    import pygame
except ModuleNotFoundError:  # pragma: no cover - optional dependency guard
    pygame = None  # type: ignore[assignment]

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
from .rolling_score import RollingScore
from .renderer import Renderer
from .types import Action, ControllerType, Observation, Player


@dataclass(frozen=True)
class AgentFeedback:
    """Stores the feedback required to update an agent after a tick."""

    controller: AIController
    reward: float
    next_observation: Observation


class Game:
    """Encapsulates the Collect game runtime."""

    _RANDOMIZATION_INTERVAL_SECONDS = 5 * 60.0
    _ROLLING_SCORE_WINDOW_SECONDS = 5 * 60.0

    def __init__(self, player_count: int = DEFAULT_PLAYER_COUNT) -> None:
        if pygame is None:
            raise RuntimeError("pygame is required to run the Collect game loop; install pygame to continue")
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
        self._next_randomization_time = time.time() + self._RANDOMIZATION_INTERVAL_SECONDS
        self._rolling_score = RollingScore(self._ROLLING_SCORE_WINDOW_SECONDS)

    def run(self) -> None:
        while self._running:
            self._escape_stage = 0
            round_end_time = time.time() + ROUND_SECONDS
            round_active = True
            paused = False
            while round_active and self._running:
                remaining_time = round_end_time - time.time()
                if remaining_time <= 0:
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
                self._maybe_randomize_lowest_agent(time.time())
                if paused:
                    epsilon_status = self._epsilon_by_player()
                    rolling_status = self._rolling_scores_by_player(time.time())
                    self._renderer.draw(
                        self._state.players,
                        self._state.resources,
                        self._state.monster,
                        self._state.target,
                        remaining_time,
                        paused,
                        rolling_status,
                        epsilon_status,
                    )
                    self._clock.tick(FRAME_RATE)
                    continue
                feedback = self._tick_players()
                remaining_time = max(0.0, round_end_time - time.time())
                is_terminal = remaining_time <= 0.0
                self._apply_agent_feedback(feedback, is_terminal)
                epsilon_status = self._epsilon_by_player()
                rolling_status = self._rolling_scores_by_player(time.time())
                self._renderer.draw(
                    self._state.players,
                    self._state.resources,
                    self._state.monster,
                    self._state.target,
                    remaining_time,
                    paused,
                    rolling_status,
                    epsilon_status,
                )
                self._clock.tick(FRAME_RATE)
                if is_terminal:
                    round_active = False
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

    def _tick_players(self) -> List[AgentFeedback]:
        feedback: List[AgentFeedback] = []
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
            updated_player = self._state.players[index]
            score_delta = updated_player.score - player.score
            if score_delta > 0:
                self._rolling_score.record(player.identifier, time.time(), score_delta)
            controller = self._ai_controllers.get(player.identifier)
            if controller is not None and self._human_player_identifier != player.identifier:
                next_observation = Observation(
                    player=self._state.players[index],
                    players=self._state.players,
                    resources=self._state.resources,
                    monster=self._state.monster,
                    target=self._state.target,
                )
                feedback.append(
                    AgentFeedback(
                        controller=controller,
                        reward=reward,
                        next_observation=next_observation,
                    )
                )
        self._state.advance_environment()
        return feedback

    def _apply_agent_feedback(self, feedback: List[AgentFeedback], is_terminal: bool) -> None:
        for transition in feedback:
            transition.controller.observe(transition.reward, transition.next_observation, is_terminal)

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
            epsilon_status = self._epsilon_by_player()
            rolling_status = self._rolling_scores_by_player(time.time())
            self._renderer.draw(
                self._state.players,
                self._state.resources,
                self._state.monster,
                self._state.target,
                remaining,
                paused=True,
                rolling_scores=rolling_status,
                epsilon_percentages=epsilon_status,
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

    def _epsilon_by_player(self) -> dict[int, float] | None:
        if not self._ai_controllers:
            return None
        values: dict[int, float] = {}
        for identifier, controller in self._ai_controllers.items():
            exploration_rate = controller.exploration_rate()
            if exploration_rate is None:
                continue
            values[identifier] = exploration_rate * 100.0
        if not values:
            return None
        return values

    def _rolling_scores_by_player(self, current_time: float) -> dict[int, int] | None:
        if not hasattr(self, "_rolling_score"):
            return None
        totals = self._rolling_score.totals(current_time)
        if not totals:
            return None
        return totals

    def _maybe_randomize_lowest_agent(self, current_time: float) -> None:
        if not hasattr(self, "_next_randomization_time"):
            self._next_randomization_time = current_time + self._RANDOMIZATION_INTERVAL_SECONDS
            return
        if current_time < self._next_randomization_time:
            return
        self._next_randomization_time = current_time + self._RANDOMIZATION_INTERVAL_SECONDS
        if not hasattr(self, "_state"):
            return
        if not hasattr(self, "_ai_controllers"):
            return
        players = getattr(self._state, "players", ())
        if not players:
            return
        candidates: List[Tuple[float, AIController]] = []
        for player in players:
            if self._human_player_identifier == player.identifier:
                continue
            controller = self._ai_controllers.get(player.identifier)
            if controller is None:
                continue
            rolling_total = (
                float(self._rolling_score.total(player.identifier, current_time))
                if hasattr(self, "_rolling_score")
                else 0.0
            )
            score_with_jitter = rolling_total + random.random()
            candidates.append((score_with_jitter, controller))
        if not candidates:
            return
        candidates.sort(key=lambda entry: entry[0])
        controller = candidates[0][1]
        if hasattr(controller, "randomize_agent_percentile"):
            controller.randomize_agent_percentile(50.0)
        elif hasattr(controller, "randomize_agent"):
            controller.randomize_agent()

        remaining_controllers = [entry[1] for entry in candidates[1:]]
        if not remaining_controllers:
            return
        selected = random.choice(remaining_controllers)
        if hasattr(selected, "randomize_agent_percentile"):
            selected.randomize_agent_percentile(20.0)
        elif hasattr(selected, "randomize_agent"):
            selected.randomize_agent()

