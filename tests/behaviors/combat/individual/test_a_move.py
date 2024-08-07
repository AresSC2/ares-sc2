from pathlib import Path

import pytest
from sc2.position import Point2
from sc2.unit import Unit

from ares import AresBot
from ares.behaviors.combat.individual import AMove

pytest_plugins = ("pytest_asyncio",)

MAPS: list[Path] = [
    map_path
    for map_path in (
        Path(__file__).parent.parent.parent.parent / "pickle_data"
    ).iterdir()
    if map_path.suffix == ".xz"
]


@pytest.mark.parametrize("bot", MAPS, indirect=True)
class TestAMove:
    def test_a_move(self, bot: AresBot, event_loop):
        # simple test, a move should always return True
        unit: Unit = bot.workers[0]
        target: Point2 = bot.game_info.map_center
        # unit present in ability tracker
        assert AMove(unit, target).execute(bot, bot.config, bot.mediator)
