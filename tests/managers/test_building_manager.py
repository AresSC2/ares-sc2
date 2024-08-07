from pathlib import Path

import pytest
from sc2.ids.unit_typeid import UnitTypeId as UnitID
from sc2.unit import Unit

from ares import AresBot
from ares.consts import UnitRole
from ares.managers.building_manager import BuildingManager

pytest_plugins = ("pytest_asyncio",)

MAPS: list[Path] = [
    map_path
    for map_path in (Path(__file__).parent.parent / "pickle_data").iterdir()
    if map_path.suffix == ".xz"
]


@pytest.mark.parametrize("bot", MAPS, indirect=True)
class TestBuildingManager:
    scenarios = [(map_path.name, {"map_path": map_path}) for map_path in MAPS]

    def test_add_to_build_tracker(self, bot: AresBot, event_loop):
        """
        Test that we found some placements at every expansion
        """
        # arrange
        building_manager: BuildingManager = bot.manager_hub.building_manager
        worker: Unit = bot.workers[0]

        # act
        building_manager.build_with_specific_worker(
            worker, UnitID.COMMANDCENTER, bot.mediator.get_own_nat
        )

        # assert
        tracker = building_manager.building_tracker
        assert worker.tag in tracker
        assert tracker[worker.tag]["id"] == UnitID.COMMANDCENTER
        assert building_manager.building_counter[UnitID.COMMANDCENTER] == 1
        assert (
            worker.tag
            in bot.manager_hub.unit_role_manager.unit_role_dict[UnitRole.BUILDING]
        )

    def test_remove_unit(self, bot: AresBot, event_loop):
        # arrange
        building_manager: BuildingManager = bot.manager_hub.building_manager
        worker: Unit = bot.workers[0]
        tracker = building_manager.building_tracker

        # act
        building_manager.build_with_specific_worker(
            worker, UnitID.COMMANDCENTER, bot.mediator.get_own_nat
        )
        assert worker.tag in tracker
        building_manager.remove_unit(worker.tag)

        assert worker.tag not in tracker

    @pytest.mark.asyncio
    async def test_is_pending(self, bot: AresBot, event_loop):
        # arrange
        building_manager: BuildingManager = bot.manager_hub.building_manager
        worker: Unit = bot.workers[0]
        building_manager.build_with_specific_worker(
            worker, UnitID.COMMANDCENTER, bot.mediator.get_own_nat
        )

        # act
        assert building_manager.is_pending(UnitID.COMMANDCENTER, 1)
