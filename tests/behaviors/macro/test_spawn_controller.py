from __future__ import annotations

from unittest.mock import MagicMock

from sc2.game_data import Cost
from sc2.ids.unit_typeid import UnitTypeId

from ares.behaviors.macro import SpawnController

ARMY_COMP: dict[UnitTypeId, dict[str, float | int]] = {
    UnitTypeId.MARINE: {"proportion": 0.35, "priority": 2},
    UnitTypeId.MEDIVAC: {"proportion": 0.35, "priority": 1},
    UnitTypeId.SIEGETANK: {"proportion": 0.3, "priority": 0},
}

COSTS: dict[UnitTypeId, Cost] = {
    UnitTypeId.MARINE: Cost(50, 0),
    UnitTypeId.MEDIVAC: Cost(100, 100),
    UnitTypeId.SIEGETANK: Cost(150, 125),
}

SUPPLY: dict[UnitTypeId, float] = {
    UnitTypeId.MARINE: 1,
    UnitTypeId.MEDIVAC: 2,
    UnitTypeId.SIEGETANK: 3,
}


def _setup(unit_counts: dict[UnitTypeId, int]) -> tuple[MagicMock, MagicMock, dict]:
    """Mock a bot with plenty of resources and one idle structure per unit type.

    Returns the bot, mediator and a dict of unit type -> structure mock,
    so tests can inspect which structures were told to train.
    """
    structures: dict[UnitTypeId, MagicMock] = {
        type_id: MagicMock(name=f"{type_id.name}_producer") for type_id in ARMY_COMP
    }

    ai = MagicMock()
    ai.state.upgrades = set()
    ai.supply_left = 200
    ai.minerals = 10_000
    ai.vespene = 10_000
    ai.num_larva_left = 0
    ai.tech_ready_for_unit.return_value = True
    ai.can_afford.return_value = True
    ai.cost_dict = COSTS
    ai.calculate_supply_cost.side_effect = lambda type_id: SUPPLY[type_id]
    # a fresh list each call, as the spawn controller pops from it
    ai.get_build_structures.side_effect = lambda _from, type_id, *_args: [
        structures[type_id]
    ]

    mediator = MagicMock()
    mediator.get_own_unit_count.side_effect = lambda unit_type_id: unit_counts[
        unit_type_id
    ]

    return ai, mediator, structures


class TestSpawnController:
    def test_exact_composition_still_spawns(self):
        # arrange: 7 / 7 / 6 out of 20 matches 0.35 / 0.35 / 0.3 exactly
        ai, mediator, structures = _setup(
            {
                UnitTypeId.MARINE: 7,
                UnitTypeId.MEDIVAC: 7,
                UnitTypeId.SIEGETANK: 6,
            }
        )

        # act
        did_action: bool = SpawnController(ARMY_COMP).execute(ai, {}, mediator)

        # assert
        assert did_action
        for type_id, structure in structures.items():
            structure.train.assert_called_once_with(type_id)

    def test_over_represented_unit_is_not_spawned(self):
        # arrange: too many marines, everything else under target
        ai, mediator, structures = _setup(
            {
                UnitTypeId.MARINE: 12,
                UnitTypeId.MEDIVAC: 4,
                UnitTypeId.SIEGETANK: 4,
            }
        )

        # act
        did_action: bool = SpawnController(ARMY_COMP).execute(ai, {}, mediator)

        # assert
        assert did_action
        structures[UnitTypeId.MARINE].train.assert_not_called()
        structures[UnitTypeId.MEDIVAC].train.assert_called_once_with(UnitTypeId.MEDIVAC)
        structures[UnitTypeId.SIEGETANK].train.assert_called_once_with(
            UnitTypeId.SIEGETANK
        )
