from pathlib import Path

import numpy as np
import pytest
from map_analyzer import MapData
from sc2.unit import Unit

from ares import AresBot
from ares.behaviors.combat.individual import KeepUnitSafe

pytest_plugins = ("pytest_asyncio",)

MAPS: list[Path] = [
    map_path
    for map_path in (
        Path(__file__).parent.parent.parent.parent / "pickle_data"
    ).iterdir()
    if map_path.suffix == ".xz"
]


@pytest.mark.parametrize("bot", MAPS, indirect=True)
class TestKeepUnitSafe:
    def test_keep_unit_safe(self, bot: AresBot, event_loop):
        # arrange
        unit: Unit = bot.workers[0]
        danger_grid: np.ndarray = bot.mediator.get_ground_grid
        safe_grid: np.ndarray = danger_grid.copy()

        # add some danger to danger grid
        map_data: MapData = bot.mediator.get_map_data_object
        danger_grid = map_data.add_cost(unit.position, 5.0, danger_grid, 25.0)

        # action should be issued as unit in danger
        assert KeepUnitSafe(unit, danger_grid).execute(bot, bot.config, bot.mediator)
        # no action should be issued on safe grid
        assert not KeepUnitSafe(unit, safe_grid).execute(bot, bot.config, bot.mediator)
