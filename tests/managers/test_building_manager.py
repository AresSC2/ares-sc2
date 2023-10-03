from pathlib import Path

import pytest
from sc2.ids.unit_typeid import UnitTypeId as UnitID
from sc2.unit import Unit

from ares import AresBot
from ares.consts import UnitRole
from ares.managers.building_manager import BuildingManager
from tests.load_bot_from_pickle import build_bot_object_from_pickle_data

pytest_plugins = ("pytest_asyncio",)

MAPS: list[Path] = [
    map_path
    for map_path in (Path(__file__).parent.parent / "pickle_data").iterdir()
    if map_path.suffix == ".xz"
]


def pytest_generate_tests(metafunc):
    idlist = []
    argvalues = []
    for scenario in metafunc.cls.scenarios:
        idlist.append(scenario[0])
        items = scenario[1].items()
        argnames = [x[0] for x in items]
        argvalues.append(([x[1] for x in items]))
    metafunc.parametrize(argnames, argvalues, ids=idlist, scope="class")


class TestBuildingManager:
    scenarios = [(map_path.name, {"map_path": map_path}) for map_path in MAPS]

    @pytest.mark.asyncio
    async def test_add_to_build_tracker(self, map_path: Path):
        """
        Test that we found some placements at every expansion
        """
        # arrange
        bot: AresBot = await build_bot_object_from_pickle_data(map_path)
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
