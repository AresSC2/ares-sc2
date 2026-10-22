from __future__ import annotations

from unittest.mock import MagicMock, patch

from sc2.data import Race
from sc2.ids.unit_typeid import UnitTypeId

from ares.behaviors.macro import BuildWorkers

SPAWN_CONTROLLER_PATH: str = "ares.behaviors.macro.build_workers.SpawnController"


def _setup(race: Race, worker_type: UnitTypeId, supply_workers: int) -> MagicMock:
    ai = MagicMock()
    ai.race = race
    ai.worker_type = worker_type
    ai.supply_workers = supply_workers
    ai.can_afford.return_value = True
    return ai


class TestBuildWorkers:
    def test_zerg_does_not_overshoot_to_count(self):
        # arrange: lots of larva, but only 2 drones short of the target
        ai = _setup(Race.Zerg, UnitTypeId.DRONE, supply_workers=78)
        ai.larva = [MagicMock() for _ in range(20)]

        # act
        with patch(SPAWN_CONTROLLER_PATH) as spawn_controller:
            BuildWorkers(to_count=80).execute(ai, {}, MagicMock())

        # assert
        spawn_controller.assert_called_once()
        assert spawn_controller.call_args.kwargs["maximum"] == 2

    def test_zerg_builds_drones_when_townhalls_busy(self):
        # arrange: hatcheries are busy (ie: making queens), but larva is available
        ai = _setup(Race.Zerg, UnitTypeId.DRONE, supply_workers=30)
        ai.larva = [MagicMock()]
        ai.townhalls.idle = []

        # act
        with patch(SPAWN_CONTROLLER_PATH) as spawn_controller:
            BuildWorkers(to_count=80).execute(ai, {}, MagicMock())

        # assert
        spawn_controller.return_value.execute.assert_called_once()

    def test_no_workers_at_to_count(self):
        # arrange
        ai = _setup(Race.Terran, UnitTypeId.SCV, supply_workers=80)
        ai.townhalls.idle = [MagicMock()]

        # act
        with patch(SPAWN_CONTROLLER_PATH) as spawn_controller:
            did_action: bool = BuildWorkers(to_count=80).execute(ai, {}, MagicMock())

        # assert
        assert not did_action
        spawn_controller.assert_not_called()
