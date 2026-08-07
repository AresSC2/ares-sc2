from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest
from sc2.ids.unit_typeid import UnitTypeId

from ares import AresBot
from ares.build_runner.build_order_runner import BuildOrderRunner
from ares.consts import BUILDS, OPENING_BUILD_ORDER
from tests.mock_config import MOCK_CONFIG

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

    @pytest.mark.asyncio
    async def test_switch_opening_resets_build_completed(
        self, bot: AresBot, event_loop
    ):
        build_runner: BuildOrderRunner = bot.build_order_runner

        config: dict = deepcopy(MOCK_CONFIG)
        config[BUILDS] = {
            "test_opening_one": {OPENING_BUILD_ORDER: ["10 supply"]},
            "test_opening_two": {OPENING_BUILD_ORDER: ["10 supply"]},
        }
        build_runner.config = config
        # attributes normally set in AresBot `on_before_start`, missing from
        # the pickled test bot
        bot.supply_type = UnitTypeId.SUPPLYDEPOT
        bot.gas_type = UnitTypeId.REFINERY
        bot.base_townhall_type = UnitTypeId.COMMANDCENTER

        build_runner.switch_opening("test_opening_one")
        assert build_runner.chosen_opening == "test_opening_one"
        assert not build_runner.build_completed
        build_runner.set_build_completed()
        assert build_runner.build_completed

        build_runner.switch_opening("test_opening_two")
        assert build_runner.chosen_opening == "test_opening_two"
        assert not build_runner.build_completed
