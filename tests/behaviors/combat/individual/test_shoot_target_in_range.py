from pathlib import Path

import pytest
from sc2.unit import Unit

from ares import AresBot
from ares.behaviors.combat.individual import ShootTargetInRange

pytest_plugins = ("pytest_asyncio",)

MAPS: list[Path] = [
    map_path
    for map_path in (
        Path(__file__).parent.parent.parent.parent / "pickle_data"
    ).iterdir()
    if map_path.suffix == ".xz"
]


@pytest.mark.parametrize("bot", MAPS, indirect=True)
class TestShootTargetInRange:
    def test_shoot_target_in_range(self, bot: AresBot, event_loop):
        # arrange
        unit: Unit = bot.workers[0]

        # no action as there are no enemy in range
        assert not ShootTargetInRange(unit, bot.enemy_units).execute(
            bot, bot.config, bot.mediator
        )
