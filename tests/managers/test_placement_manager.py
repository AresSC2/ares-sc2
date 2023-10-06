from pathlib import Path

import pytest
from sc2.position import Point2

from ares import AresBot
from ares.consts import BuildingSize
from ares.managers.placement_manager import PlacementManager

pytest_plugins = ("pytest_asyncio",)

MAPS: list[Path] = [
    map_path
    for map_path in (Path(__file__).parent.parent / "pickle_data").iterdir()
    if map_path.suffix == ".xz"
]


@pytest.mark.parametrize("bot", MAPS, indirect=True)
class TestPlacementManager:
    scenarios = [(map_path.name, {"map_path": map_path}) for map_path in MAPS]

    def test_placements_found(self, bot: AresBot, event_loop):
        """
        Test that we found some placements at every expansion
        """
        placement_manager: PlacementManager = bot.manager_hub.placement_manager
        if len(bot.expansion_locations_list) >= 2:
            placements_dict: dict[
                Point2, dict[BuildingSize, dict]
            ] = placement_manager.placements_dict
            for el, placements in placements_dict.items():
                assert len(placements[BuildingSize.TWO_BY_TWO]) >= 1
                assert len(placements[BuildingSize.THREE_BY_THREE]) >= 1
