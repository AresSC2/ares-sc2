from pathlib import Path

import pytest
from sc2.position import Point2

from ares import AresBot
from ares.consts import BuildingSize
from ares.managers.placement_manager import PlacementManager
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


class TestPlacementManager:
    scenarios = [(map_path.name, {"map_path": map_path}) for map_path in MAPS]

    @pytest.mark.asyncio
    async def test_placements_found(self, map_path: Path):
        """
        Test that we found some placements at every expansion
        """
        bot: AresBot = await build_bot_object_from_pickle_data(map_path)
        placement_manager: PlacementManager = bot.manager_hub.placement_manager
        if len(bot.expansion_locations_list) >= 2:
            placements_dict: dict[
                Point2, dict[BuildingSize, dict]
            ] = placement_manager.placements_dict
            for el, placements in placements_dict.items():
                assert len(placements[BuildingSize.TWO_BY_TWO]) >= 1
                assert len(placements[BuildingSize.THREE_BY_THREE]) >= 1
