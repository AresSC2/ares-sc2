"""Handle data."""
import json
from os import path
from typing import Any, Dict, List, Optional, Union

from consts import (
    BUILD_CYCLE,
    CYCLE,
    DATA_DIR,
    DEBUG,
    DURATION,
    ENEMY_RUSHED,
    LOSS,
    RACE,
    RESULT,
    STRATEGY_USED,
    TEST_OPPONENT_ID,
    USE_DATA,
    WIN,
    BotMode,
    ManagerName,
    ManagerRequestType,
)
from custom_bot_ai import CustomBotAI
from managers.manager import Manager
from managers.manager_mediator import IManagerMediator, ManagerMediator
from sc2.data import Result


class DataManager(Manager, IManagerMediator):
    """
    Handles opponent data, and chooses a strategy, based on the
    build cycle in config.yaml
    """

    def __init__(
        self, ai: CustomBotAI, config: Dict, mediator: ManagerMediator
    ) -> None:
        super().__init__(ai, config, mediator)
        self.manager_requests_dict = {
            ManagerRequestType.GET_INITIAL_BOT_MODE: lambda kwargs: self.starting_bot_mode
        }

        self.build_cycle: List[BotMode] = self.get_build_cycle()
        self.starting_bot_mode: BotMode = BotMode.DEFAULT
        self.found_build: bool = False
        self.opponent_history: List = []

        self.file_path: path = path.join(
            DATA_DIR, "{}.json".format(self.ai.opponent_id)
        )

        self.data_saved: bool = False

        if self.config[USE_DATA]:
            self.get_opponent_data(self.ai.opponent_id)
            self.choose_bot_mode()

        else:
            self.starting_bot_mode = self.build_cycle[0]

    def manager_request(
        self,
        receiver: ManagerName,
        request: ManagerRequestType,
        reason: str = None,
        **kwargs
    ) -> Optional[Union[BotMode, List[BotMode]]]:
        """Fetch information from this Manager so another Manager can use it.

        Parameters
        ----------
        receiver :
            This Manager.
        request :
            What kind of request is being made
        reason :
            Why the reason is being made
        kwargs :
            Additional keyword args if needed for the specific request, as determined
            by the function signature (if appropriate)

        Returns
        -------
        Optional[Union[BotMode, List[BotMode]]] :
            Either one of the ability dictionaries is being returned or a function that
            returns None was called from a different manager (please don't do that).

        """
        return self.manager_requests_dict[request](kwargs)

    async def update(self, _iteration: int) -> None:
        """Not used by this manager.

        Manager is an abstract class and must have an ``update`` method.

        Parameters
        ----------
        _iteration :
            The current game iteration

        Returns
        -------

        """
        pass

    def choose_bot_mode(self) -> None:
        """
        Look at the last build used, and choose a strategy depending on result
        TODO: Develop a more sophisticated system rather then cycling on defeat
        @return:
        """
        last_build: str = self.opponent_history[-1][STRATEGY_USED]
        last_result: int = self.opponent_history[-1][RESULT]

        for i, build in enumerate(self.build_cycle):
            if last_build == build.name:
                self.found_build = True
                # Defeat
                if last_result == 0:
                    index: int = 0 if len(self.build_cycle) <= i + 1 else i + 1
                    self.starting_bot_mode = self.build_cycle[index]
                else:
                    self.starting_bot_mode = build
                break
        # incase build from last game wasn't found in build cycle
        if not self.found_build:
            self.starting_bot_mode = self.build_cycle[0]

        self.starting_bot_mode = self.starting_bot_mode

    def get_build_cycle(self) -> List[BotMode]:
        """
        Get the build cycle for the opponent from the config file
        If the opponent id is not present, set a default build cycle instead
        @return:
        """
        if self.config[DEBUG]:
            opponent_id: str = TEST_OPPONENT_ID
        else:
            opponent_id: str = self.ai.opponent_id

        build_cycle: List[BotMode] = []
        # get a build cycle from config depending on ai arena opponent id
        if opponent_id in self.config[BUILD_CYCLE]:
            for build in self.config[BUILD_CYCLE][opponent_id][CYCLE]:
                build_cycle.append(BotMode[build])
        # else choose a cycle depending on the enemy race
        elif self.ai.enemy_race.name in self.config[BUILD_CYCLE]:
            for build in self.config[BUILD_CYCLE][self.ai.enemy_race.name][CYCLE]:
                build_cycle.append(BotMode[build])
        # shouldn't happen, but make sure we have something just in case
        else:
            build_cycle.append(BotMode.DEFAULT)

        return build_cycle

    def get_opponent_data(self, _opponent_id: str) -> None:
        """
        Get saved data on opponent, if none is present setup new data
        @param _opponent_id:
        @return:
        """
        if path.isfile(self.file_path):
            with open(self.file_path, "r") as f:
                self.opponent_history = json.load(f)
        else:
            # no data, create a dummy version
            self.opponent_history = [
                {
                    RACE: str(self.ai.enemy_race),
                    DURATION: 0,
                    ENEMY_RUSHED: False,
                    STRATEGY_USED: self.build_cycle[0].name,
                    RESULT: 2,
                }
            ]

    def store_opponent_data(self, result: Union[Result, str]) -> None:
        """
        Called at end of game, save build used and result.
        @param result:
        @return:
        """
        # only write results once
        if self.data_saved:
            return
        if type(result) != str:
            result_id: int = 1
            if result == Result.Victory:
                result_id = 2
            elif result == Result.Defeat:
                result_id = 0
        else:
            if result == WIN:
                result_id = 2
            elif result == LOSS:
                result_id = 0
            else:
                # treat it as a tie if we don't know what happened
                result_id = 1

        self.add_game_to_dict(
            self.starting_bot_mode, False, int(self.ai.time), result_id
        )
        with open(self.file_path, "w") as f:
            json.dump(self.opponent_history, f)
        self.data_saved = True

    def add_game_to_dict(
        self, bot_mode: BotMode, enemy_rushed: bool, game_duration: int, result: int
    ) -> None:
        """
        Append a new game to the dict's list
        @param bot_mode:
        @param enemy_rushed:
        @param game_duration:
        @param result:
        @return:
        """
        game = {
            RACE: str(self.ai.enemy_race),
            DURATION: game_duration,
            ENEMY_RUSHED: enemy_rushed,
            STRATEGY_USED: bot_mode.name,
            RESULT: result,
        }
        self.opponent_history.append(game)