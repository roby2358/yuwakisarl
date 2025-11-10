from __future__ import annotations

import pytest

from collect.config import FIELD_DIMENSIONS
from collect.types import ControllerType, Observation, Player


def _make_player(identifier: int, position: tuple[int, int], *, has_resource: bool = False) -> Player:
    return Player(
        identifier=identifier,
        position=position,
        controller=ControllerType.AI,
        has_resource=has_resource,
    )


def test_observation_vector_encodes_relative_offsets() -> None:
    player = _make_player(0, (10, 10))
    other_player = _make_player(1, (7, 8))
    resources = ((12, 11), (50, 50))
    target = (20, 5)
    monster = (11, 25)

    observation = Observation(
        player=player,
        players=(player, other_player),
        resources=resources,
        target=target,
        monster=monster,
    )

    vector = observation.as_vector()

    width_span = FIELD_DIMENSIONS.width - 1
    height_span = FIELD_DIMENSIONS.height - 1

    assert len(vector) == Observation.vector_length()
    assert vector[0] == pytest.approx((12 - 10) / width_span)
    assert vector[1] == pytest.approx((11 - 10) / height_span)
    assert vector[2] == pytest.approx((20 - 10) / width_span)
    assert vector[3] == pytest.approx((5 - 10) / height_span)
    assert vector[4] == pytest.approx((7 - 10) / width_span)
    assert vector[5] == pytest.approx((8 - 10) / height_span)
    assert vector[6] == pytest.approx((11 - 10) / width_span)
    assert vector[7] == pytest.approx((25 - 10) / height_span)
    assert vector[8] == pytest.approx(0.0)


def test_observation_vector_defaults_when_data_missing() -> None:
    player = _make_player(0, (0, 0), has_resource=True)
    observation = Observation(
        player=player,
        players=(player,),
        resources=(),
        target=(0, 0),
        monster=(0, 0),
    )

    vector = observation.as_vector()

    assert vector[:8] == (0.0,) * 8
    assert vector[8] == pytest.approx(1.0)

