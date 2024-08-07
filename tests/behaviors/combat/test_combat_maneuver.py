from pathlib import Path

import numpy as np
import pytest
from sc2.unit import Unit

from ares import AresBot
from ares.behaviors.combat import CombatManeuver
from ares.behaviors.combat.individual import (
    AMove,
    AttackTarget,
    KeepUnitSafe,
    ShootTargetInRange,
    StutterUnitBack,
    StutterUnitForward,
)

pytest_plugins = ("pytest_asyncio",)

MAPS: list[Path] = [
    map_path
    for map_path in (Path(__file__).parent.parent.parent / "pickle_data").iterdir()
    if map_path.suffix == ".xz"
]


@pytest.mark.parametrize("bot", MAPS, indirect=True)
class TestCombatManeuver:
    def test_combat_maneuver(self, bot: AresBot, event_loop):

        # arrange
        maneuver: CombatManeuver = CombatManeuver()
        unit: Unit = bot.workers[0]
        grid: np.ndarray = bot.mediator.get_ground_grid

        # act
        maneuver.add(AMove(unit, bot.game_info.map_center))
        maneuver.add(KeepUnitSafe(unit, grid))
        maneuver.add(StutterUnitBack(unit, bot.enemy_units[0]))
        maneuver.add(ShootTargetInRange(unit, bot.enemy_units))
        maneuver.add(AttackTarget(unit, bot.enemy_units[0]))
        maneuver.add(StutterUnitForward(unit, bot.enemy_units[0]))

        # assert
        assert len(maneuver.micros) == 6
        # ensure they are in the order we expect
        assert isinstance(maneuver.micros[0], AMove)
        assert isinstance(maneuver.micros[1], KeepUnitSafe)
        assert isinstance(maneuver.micros[2], StutterUnitBack)
        assert isinstance(maneuver.micros[3], ShootTargetInRange)
        assert isinstance(maneuver.micros[4], AttackTarget)
        assert isinstance(maneuver.micros[5], StutterUnitForward)
