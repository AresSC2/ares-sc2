"""
This "bot" will loop over several available ladder maps and generate the pickle files.
Thanks to burny's `python-sc2` where most of this logic was taken from.
TODO: Make this pickle `ares` specific stuff (manager hub?) so we can run tests.
"""
import lzma
import os
import pickle
import sys
from os.path import abspath, dirname
from typing import Optional

from loguru import logger
from s2clientprotocol import sc2api_pb2 as sc_pb
from sc2 import maps
from sc2.data import Difficulty, Race
from sc2.main import run_game
from sc2.player import Bot, Computer
from sc2.protocol import ProtocolError

from ares import AresBot

# This allows Ares to be imported
d = dirname(dirname(abspath(__file__)))
sys.path.append(f"{d}\\")
sys.path.append(f"{d}\\src")


class ExporterBot(AresBot):
    def __init__(self, game_step_override: Optional[int] = None):
        super().__init__(game_step_override)
        self.map_name: str = None

    async def on_step(self, iteration):
        await super(ExporterBot, self).on_step(iteration)
        if iteration == 4:
            # file_path = self.get_pickle_file_path()
            # logger.info(f"Saving pickle file to {file_path}.xz")
            # await self.store_data_to_file(file_path)
            #
            file_path = self.get_pickle_file_path()
            logger.info(f"Saving pickle file to {file_path}.xz")
            await self.store_data_to_file(file_path)
            await self.client.leave()

    def get_combat_file_path(self) -> str:
        folder_path = os.path.dirname(__file__)
        subfolder_name = "combat_pickle_data"
        file_name = f"{self.map_name}.xz"
        file_path = os.path.join(folder_path, subfolder_name, file_name)
        return file_path

    def get_pickle_file_path(self) -> str:
        folder_path = os.path.dirname(__file__)
        subfolder_name = "pickle_data"
        file_name = f"{self.map_name}.xz"
        file_path = os.path.join(folder_path, subfolder_name, file_name)
        return file_path

    async def store_data_to_file(self, file_path: str):
        # Grab all raw data from observation
        raw_game_data = await self.client._execute(
            data=sc_pb.RequestData(
                ability_id=True,
                unit_type_id=True,
                upgrade_id=True,
                buff_id=True,
                effect_id=True,
            )
        )

        raw_game_info = await self.client._execute(game_info=sc_pb.RequestGameInfo())

        raw_observation = self.state.response_observation

        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        try:
            with lzma.open(file_path, "wb") as f:
                pickle.dump([raw_game_data, raw_game_info, raw_observation], f)
        except Exception as e:
            print(e)

    async def on_start(self):
        await super(ExporterBot, self).on_start()
        # Make map visible
        await self.client.debug_show_map()
        await self.client.debug_control_enemy()
        await self.client.debug_god()

        # Spawn one of each unit
        # TODO: Create some scenarios to test units here
        #   This current logic, means all pathing breaks in pickle tests
        # valid_units: Set[UnitTypeId] = {
        #     UnitTypeId(unit_id)
        #     for unit_id, data in self.game_data.units.items()
        #     if data._proto.race != Race.NoRace
        #     and data._proto.race != Race.Random
        #     and data._proto.available
        #     # Dont cloak units
        #     and UnitTypeId(unit_id) != UnitTypeId.MOTHERSHIP
        #     and (
        #         data._proto.mineral_cost
        #         or data._proto.movement_speed
        #         or data._proto.weapons
        #     )
        # }
        #
        # # Create units for self
        # await self.client.debug_create_unit(
        #     [[valid_unit, 1, self.start_location, 1] for valid_unit in valid_units]
        # )
        # # Create units for enemy
        # await self.client.debug_create_unit(
        #     [
        #         [valid_unit, 1, self.enemy_start_locations[0], 2]
        #         for valid_unit in valid_units
        #     ]
        # )


def main():

    maps_ = [
        "GresvanAIE",
        "GoldenauraAIE",
        "InfestationStationAIE",
        "RoyalBloodAIE",
        "DragonScalesAIE",
        "AncientCisternAIE",
    ]

    for map_ in maps_:
        try:
            bot = ExporterBot()
            bot.map_name = map_
            file_path = bot.get_pickle_file_path()
            if os.path.isfile(file_path):
                logger.warning(
                    f"Pickle file for map {map_} was already generated. Skipping."
                    f" If you wish to re-generate files, please remove them first."
                )
                continue
            logger.info(f"Creating pickle file for map {map_} ...")
            run_game(
                maps.get(map_),
                [Bot(Race.Terran, bot), Computer(Race.Zerg, Difficulty.Easy)],
                realtime=False,
            )
        except ProtocolError:
            # ProtocolError appears after a leave game request
            pass
        except Exception as e:
            logger.exception(f"Caught unknown exception: {e}")
            logger.error(
                f"Map {map_} could not be found, so pickle "
                f"files for that map could not be generated. Error: {e}"
            )


if __name__ == "__main__":
    main()
