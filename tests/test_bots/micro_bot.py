import random
import sys
from os.path import abspath, dirname, join

import numpy as np
from sc2 import maps
from sc2.main import run_game
from sc2.position import Point2

# Get the directory of the current file
current_dir = dirname(__file__)

# Go two directories up
two_up = abspath(join(current_dir, "..", ".."))

# Append the src folder to the path
src_path = join(two_up, "src")

# Add the src folder to the system path
sys.path.append(src_path)

from sc2.data import Difficulty, Race
from sc2.player import Bot, Computer

from ares import AresBot
from ares.behaviors.combat import CombatManeuver
from ares.behaviors.combat.individual import AMove, KeepUnitSafe, PathUnitToTarget


class DummyBot(AresBot):
    def __init__(self):
        super().__init__()

    async def on_step(self, iteration: int):
        await super(DummyBot, self).on_step(iteration)
        # test out a few behaviors while we are here
        grid: np.ndarray = self.mediator.get_ground_grid
        target: Point2 = self.enemy_start_locations[0]
        if self.enemy_structures:
            target = self.enemy_structures[0].position

        for unit in self.units:
            maneuver: CombatManeuver = CombatManeuver()
            if self.time < 10.0:
                maneuver.add(KeepUnitSafe(unit=unit, grid=grid))
            else:
                maneuver.add(
                    PathUnitToTarget(
                        unit=unit, grid=grid, target=target, success_at_distance=10.0
                    )
                )
                maneuver.add(AMove(unit=unit, target=target))
            self.register_behavior(maneuver)

    async def on_start(self) -> None:
        await super(DummyBot, self).on_start()


# Start game
if __name__ == "__main__":
    random_map = random.choice(
        [
            "BotMicroArena_6",
        ]
    )
    run_game(
        maps.get(random_map),
        [
            Bot(Race.Random, DummyBot(), "DummyBot"),
            Computer(Race.Protoss, Difficulty.CheatInsane),
        ],
        realtime=False,
    )
