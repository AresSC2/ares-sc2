import asyncio
import importlib
import lzma
import pickle
import sys
from os.path import abspath, dirname
from unittest.mock import patch

from sc2.bot_ai import BotAI
from sc2.client import Client
from sc2.game_data import GameData
from sc2.game_info import GameInfo
from sc2.game_state import GameState
from sc2.ids.unit_typeid import UnitTypeId

d = dirname(dirname(abspath(__file__)))
sys.path.append(f"{d}\\")
sys.path.append(f"{d}\\src")

from ares import AresBot, BuildOrderRunner, UnitRole
from tests.mock_config import MOCK_CONFIG


async def build_bot_object_from_pickle_data(path_to_pickle_date) -> AresBot:
    """
    An admittedly hacky script to load an AresBot object from pickled data

    Parameters
    ----------
    path_to_pickle_date

    Returns
    -------

    """
    with lzma.open(path_to_pickle_date, "rb") as f:
        raw_game_data, raw_game_info, raw_observation = pickle.load(f)

    bot = BotAI()
    game_data = GameData(raw_game_data.data)
    game_info = GameInfo(raw_game_info.game_info)
    game_state = GameState(raw_observation)
    bot._initialize_variables()
    client = Client(True)

    bot._prepare_start(
        client=client, player_id=1, game_info=game_info, game_data=game_data
    )
    with patch.object(Client, "query_available_abilities_with_tag", return_value={}):
        await bot._prepare_step(state=game_state, proto_game_info=raw_game_info)
        bot._prepare_first_step()

        ares = importlib.import_module("ares.main")
        bot.__class__ = ares.AresBot
        bot.config = MOCK_CONFIG
        bot.enemy_parasitic_bomb_positions = []
        bot.unit_tag_dict = {}
        for unit in bot.all_units:
            bot.unit_tag_dict[unit.tag] = unit
        bot.actual_iteration = 5
        bot.arcade_mode = False
        bot.worker_type = UnitTypeId.SCV
        bot.register_managers()
        bot.ready_townhalls = bot.townhalls
        bot._same_order_actions = []
        bot.build_order_runner = BuildOrderRunner(bot, "fd", MOCK_CONFIG, bot.mediator)
        bot.chat_debug = False
        for worker in bot.workers:
            bot.mediator.assign_role(tag=worker.tag, role=UnitRole.GATHERING)
        await bot.on_step(5)
    return bot


if __name__ == "__main__":
    path = "tests/pickle_data/InfestationStationAIE.xz"
    bot = asyncio.run(build_bot_object_from_pickle_data(path))
    print(bot)
