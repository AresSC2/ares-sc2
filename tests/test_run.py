"""
See if the AresBot starts.

Starts as a random race and speed mines with 12 workers.

"""

import random
import sys
from os import path
from os.path import abspath, dirname
from pathlib import Path
from typing import List

import yaml

d = dirname(dirname(abspath(__file__)))
sys.path.append(f"{d}\\")
sys.path.append(f"{d}\\src")

from sc2 import maps
from sc2.data import AIBuild, Difficulty, Race
from sc2.main import run_game
from sc2.player import Bot, Computer

from src.ares.behaviors.macro.mining import Mining
from src.ares.main import AresBot

# change if non default setup / linux
# if having issues with this, modify `map_list` below manually
MAPS_PATH: str = "C:\\Program Files (x86)\\StarCraft II\\Maps"
CONFIG_FILE: str = "config.yml"
MAP_FILE_EXT: str = "SC2Map"
MY_BOT_NAME: str = "AresTestBot"
MY_BOT_RACE: str = "Random"


class TestBot(AresBot):
    __test__ = False

    async def on_start(self) -> None:
        await super(TestBot, self).on_start()

    async def on_step(self, iteration: int) -> None:
        await super(TestBot, self).on_step(iteration)
        self.register_behavior(Mining())


def main():
    bot_name: str = "AresTestBot"
    race: Race = Race.Random

    __user_config_location__: str = path.abspath(".")
    user_config_path: str = path.join(__user_config_location__, CONFIG_FILE)
    # attempt to get race and bot name from config file if they exist
    if path.isfile(user_config_path):
        with open(user_config_path) as config_file:
            config: dict = yaml.safe_load(config_file)
            if MY_BOT_NAME in config:
                bot_name = config[MY_BOT_NAME]
            if MY_BOT_RACE in config:
                race = Race[config[MY_BOT_RACE].title()]

    bot1 = Bot(race, TestBot(), bot_name)

    # Local game
    map_list: List[str] = [
        p.name.replace(f".{MAP_FILE_EXT}", "")
        for p in Path(MAPS_PATH).glob(f"*.{MAP_FILE_EXT}")
        if p.is_file()
    ]
    # alternative example code if finding the map path is problematic
    # map_list: List[str] = [
    #     "BerlingradAIE",
    #     "InsideAndOutAIE",
    #     "MoondanceAIE",
    #     "StargazersAIE",
    #     "WaterfallAIE",
    #     "HardwireAIE",
    # ]

    random_race = random.choice([Race.Zerg, Race.Terran, Race.Protoss])
    print("Starting local game...")
    run_game(
        maps.get(random.choice(map_list)),
        [
            bot1,
            Computer(random_race, Difficulty.CheatInsane, ai_build=AIBuild.Rush),
        ],
        realtime=False,
    )


# Start game
if __name__ == "__main__":
    main()
