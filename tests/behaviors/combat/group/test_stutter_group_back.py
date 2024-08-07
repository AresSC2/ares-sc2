from pathlib import Path

import pytest
from sc2.ids.unit_typeid import UnitTypeId as UnitID
from sc2.position import Point2
from sc2.unit import Unit

from ares import AresBot
from ares.behaviors.combat.group import StutterGroupBack

pytest_plugins = ("pytest_asyncio",)

MAPS: list[Path] = [
    map_path
    for map_path in (
        Path(__file__).parent.parent.parent.parent / "pickle_data"
    ).iterdir()
    if map_path.suffix == ".xz"
]


@pytest.mark.parametrize("bot", MAPS, indirect=True)
class TestStutterGroupBack:
    def test_stutter_group_back(self, bot: AresBot, event_loop):
        # simple test, a move should always return True
        units: list[Unit] = [u for u in bot.units if u.type_id != UnitID.SCV]
        target: Point2 = bot.game_info.map_center
        # should be true, as all units are able to attack
        assert StutterGroupBack(
            units,
            {u.tag for u in units},
            units[0].position,
            target,
            bot.mediator.get_ground_grid,
        ).execute(bot, bot.config, bot.mediator)
