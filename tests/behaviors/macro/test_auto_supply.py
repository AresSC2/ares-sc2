from pathlib import Path

import pytest

from ares import AresBot
from ares.behaviors.macro import AutoSupply

pytest_plugins = ("pytest_asyncio",)

MAPS: list[Path] = [
    map_path
    for map_path in (Path(__file__).parent.parent.parent / "pickle_data").iterdir()
    if map_path.suffix == ".xz"
]


@pytest.mark.parametrize("bot", MAPS, indirect=True)
class TestAutoSupply:
    def test_auto_supply(self, bot: AresBot, event_loop):
        assert AutoSupply(bot.start_location).execute(bot, bot.config, bot.mediator)
