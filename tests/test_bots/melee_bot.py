import random
import sys
from os import path

from sc2 import maps
from sc2.main import run_game

from ares import AresBot

sys.path.append(path.join(path.dirname(__file__), "../.."))

import sc2
from sc2.data import Difficulty, Race
from sc2.player import Bot, Computer

class DummyBot(AresBot):
    def __init__(self):
        super().__init__()

    async def on_step(self, iteration: int):
        pass

    async def on_start(self) -> None:
        pass


# Start game
if __name__ == "__main__":
    random_map = random.choice(
        [
        "Equilibrium513AIE",
        "Gresvan513AIE",
        "GoldenAura513AIE",
        "HardLead513AIE",
        "Oceanborn513AIE",
        "SiteDelta513AIE"
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