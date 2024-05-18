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

d = dirname(dirname(abspath(__file__)))
sys.path.append(f"{d}\\")
sys.path.append(f"{d}\\src")

from ares import AresBot
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
        bot.unit_tag_dict = {}
        bot.arcade_mode = False
        bot.register_managers()
    return bot
