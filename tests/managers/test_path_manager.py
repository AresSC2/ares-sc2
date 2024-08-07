from pathlib import Path

import numpy as np
import pytest
from sc2.ids.unit_typeid import UnitTypeId as UnitID
from sc2.position import Point2
from sc2.unit import Unit

from ares import AresBot
from ares.dicts.weight_costs import WEIGHT_COSTS
from ares.managers.path_manager import PathManager

pytest_plugins = ("pytest_asyncio",)

MAPS: list[Path] = [
    map_path
    for map_path in (Path(__file__).parent.parent / "pickle_data").iterdir()
    if map_path.suffix == ".xz"
]


@pytest.mark.parametrize("bot", MAPS, indirect=True)
class TestPathManager:
    scenarios = [(map_path.name, {"map_path": map_path}) for map_path in MAPS]

    def test_add_cost(self, bot: AresBot, event_loop):
        """
        Test that we found some placements at every expansion
        """
        path_manager: PathManager = bot.manager_hub.path_manager

        # arrange
        grid: np.ndarray = bot.mediator.get_air_grid
        pos: Point2 = bot.game_info.map_center
        cost: float = 25.0

        # ensure default value
        assert grid[pos.rounded] == 1.0

        # act
        path_manager.add_cost(pos, cost, 5.0, grid)

        # assert
        assert grid[pos.rounded] == cost + 1.0

    def test_add_cost_to_all_grids(self, bot: AresBot, event_loop):
        """
        Test that we found some placements at every expansion
        """
        path_manager: PathManager = bot.manager_hub.path_manager

        # arrange
        unit: Unit = bot.workers[0]

        # act
        # pretend influence added is a marine, for ease here
        path_manager._add_cost_to_all_grids(unit, WEIGHT_COSTS[UnitID.MARINE])

        # assert
        # check all grids that a marine cost would be added to
        air_grid = bot.mediator.get_air_grid
        air_vs_ground_grid = bot.mediator.get_air_vs_ground_grid
        grid = bot.mediator.get_ground_grid
        climber = bot.mediator.get_climber_grid

        # all grids influence should be greater then 1
        assert air_grid[unit.position.rounded] > 1.0
        assert air_vs_ground_grid[unit.position.rounded] > 1.0
        assert grid[unit.position.rounded] > 1.0
        assert climber[unit.position.rounded] > 1.0
