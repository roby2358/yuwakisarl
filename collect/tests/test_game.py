from __future__ import annotations

import pytest

from collect.ai_controller import AIController
from collect.game import AgentFeedback, Game
from collect.neural_agent import NeuralPolicyAgent
from collect.types import Action, ControllerType, Observation, Player


class DummyController:
    def __init__(self) -> None:
        self.calls: list[tuple[float, Observation, bool]] = []

    def observe(self, reward: float, next_observation: Observation, is_terminal: bool) -> None:
        self.calls.append((reward, next_observation, is_terminal))


def _observation_for(identifier: int) -> Observation:
    player = Player(identifier=identifier, position=(identifier, identifier), controller=ControllerType.AI)
    return Observation(
        player=player,
        players=(player,),
        resources=(),
        monster=(identifier + 1, identifier + 1),
        target=(identifier + 2, identifier + 2),
    )


def test_game_apply_agent_feedback_forwards_terminal_flag() -> None:
    controller = DummyController()
    terminal_observation = _observation_for(0)
    ongoing_observation = _observation_for(1)

    terminal_feedback = [
        AgentFeedback(controller=controller, reward=1.0, next_observation=terminal_observation),
    ]
    ongoing_feedback = [
        AgentFeedback(controller=controller, reward=0.25, next_observation=ongoing_observation),
    ]

    game = Game.__new__(Game)
    game._human_player_identifier = None

    game._apply_agent_feedback(terminal_feedback, True)
    game._apply_agent_feedback(ongoing_feedback, False)

    assert controller.calls == [
        (1.0, terminal_observation, True),
        (0.25, ongoing_observation, False),
    ]


def test_game_epsilon_by_player_returns_mapping() -> None:
    game = Game.__new__(Game)
    agent_a = NeuralPolicyAgent(
        state_size=Observation.vector_length(),
        action_size=len(Action),
    )
    agent_b = NeuralPolicyAgent(
        state_size=Observation.vector_length(),
        action_size=len(Action),
    )
    agent_a._epsilon_values[0] = 0.4
    agent_b._epsilon_values[1] = 0.2

    controller_a = AIController.__new__(AIController)
    controller_a.player_identifier = 0
    controller_a._agent = agent_a
    controller_b = AIController.__new__(AIController)
    controller_b.player_identifier = 1
    controller_b._agent = agent_b

    game._ai_controllers = {
        0: controller_a,
        1: controller_b,
    }

    epsilon_map = game._epsilon_by_player()

    assert epsilon_map is not None
    assert epsilon_map[0] == pytest.approx(40.0)
    assert epsilon_map[1] == pytest.approx(20.0)

