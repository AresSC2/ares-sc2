import random
import sys
from os.path import dirname, abspath, join

from sc2 import maps
from sc2.main import run_game

# Get the directory of the current file
current_dir = dirname(__file__)

# Go two directories up
two_up = abspath(join(current_dir, "..", ".."))

# Append the src folder to the path
src_path = join(two_up, "src")

# Add the src folder to the system path
sys.path.append(src_path)

from ares import AresBot

from sc2.data import Difficulty, Race
from sc2.player import Bot, Computer


class DummyBot(AresBot):
    def __init__(self):
        super().__init__()

    async def on_step(self, iteration: int):
        await super(DummyBot, self).on_step(iteration)
        for unit in self.units:
            unit.attack(self.enemy_start_locations[0])

    async def on_start(self) -> None:
        await super(DummyBot, self).on_start()


# Start game
if __name__ == "__main__":
    random_map = random.choice(
        [
            "Equilibrium513AIE",
            "Gresvan513AIE",
            "GoldenAura513AIE",
            "HardLead513AIE",
            "Oceanborn513AIE",
            "SiteDelta513AIE",
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
