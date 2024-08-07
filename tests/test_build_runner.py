"""
TODO: Work out how to test the build runner properly
"""


from pathlib import Path

import pytest

from ares import AresBot, BuildOrderRunner

pytest_plugins = ("pytest_asyncio",)

MAPS: list[Path] = [
    map_path
    for map_path in (Path(__file__).parent / "pickle_data").iterdir()
    if map_path.suffix == ".xz"
]


@pytest.mark.parametrize("bot", MAPS, indirect=True)
class TestBuildRunner:
    scenarios = [(map_path.name, {"map_path": map_path}) for map_path in MAPS]

    @pytest.mark.asyncio
    async def test_build_runner_complete(self, bot: AresBot, event_loop):
        build_runner: BuildOrderRunner = bot.build_order_runner

        build_runner.set_build_completed()
        assert build_runner.build_completed
