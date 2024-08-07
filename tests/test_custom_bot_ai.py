from pathlib import Path

import pytest

from ares import AresBot

pytest_plugins = ("pytest_asyncio",)

MAPS: list[Path] = [
    map_path
    for map_path in (Path(__file__).parent / "pickle_data").iterdir()
    if map_path.suffix == ".xz"
]


@pytest.mark.parametrize("bot", MAPS, indirect=True)
class TestCustomBotAI:
    scenarios = [(map_path.name, {"map_path": map_path}) for map_path in MAPS]

    @pytest.mark.asyncio
    async def test_get_total_supply(self, bot: AresBot, event_loop):
        assert bot.get_total_supply(bot.workers) == 15

    @pytest.mark.asyncio
    async def test_split_ground_fliers(self, bot: AresBot, event_loop):
        ground, flying = bot.split_ground_fliers(bot.workers)
        assert len(ground) == 15
        assert len(flying) == 0
