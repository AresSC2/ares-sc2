from pathlib import Path

import pytest
from sc2.unit import Unit

from ares import AresBot
from ares.behaviors.combat.individual import AttackTarget

pytest_plugins = ("pytest_asyncio",)

MAPS: list[Path] = [
    map_path
    for map_path in (
        Path(__file__).parent.parent.parent.parent / "pickle_data"
    ).iterdir()
    if map_path.suffix == ".xz"
]


@pytest.mark.parametrize("bot", MAPS, indirect=True)
class TestAttackTarget:
    def test_attack_target(self, bot: AresBot, event_loop):
        # simple test, attack target should always return True
        unit: Unit = bot.workers[0]
        target: Unit = bot.enemy_units[0]
        # unit present in ability tracker
        assert AttackTarget(unit, target).execute(bot, bot.config, bot.mediator)
