"""Handle data."""
import json
import os
from collections import defaultdict, deque
from os import path
from typing import Dict, List, Optional, Union

from loguru import logger
from sc2.data import Result

from ares.consts import (
    BUILD_CHOICES,
    BUILD_SELECTION,
    CYCLE,
    DATA_DIR,
    DEBUG,
    DURATION,
    LOSS,
    MIN_GAMES_WINRATE_BASED,
    RACE,
    RESULT,
    STRATEGY_USED,
    TEST_OPPONENT_ID,
    USE_DATA,
    WIN,
    WINRATE_BASED,
    ManagerName,
    ManagerRequestType,
)
from ares.managers.manager import Manager
from ares.managers.manager_mediator import IManagerMediator, ManagerMediator


class DataManager(Manager, IManagerMediator):
    """
    Class to handle data management and store opponent history.

    Attributes
    ----------
    manager_requests_dict : Dict[ManagerRequestType, Callable[[Any]]
        A dictionary of functions that can be requested by other managers.
    chosen_opening : str
        The chosen opening strategy for the current match.
    build_cycle : List[str]
        A list of available build strategies for the bot.
    found_build : bool
        A boolean flag indicating if the opponent's build strategy from the previous
        game was found in the build cycle.
    opponent_history : List
        A list containing the bot's previous match history against the current opponent.
    file_path : str
        The file path of the json file containing the opponent's match history.
    data_saved : bool
        A boolean flag indicating if the opponent's match history has been saved.

    Methods
    -------
    manager_request(
        self,
        receiver: ManagerName,
        request: ManagerRequestType,
        reason: str = None,
        **kwargs,
    ) -> Optional[Union[str, list[str]]]:
        Fetch information from this Manager so another Manager can use it.

    initialise(self) -> None:
        Initialize DataManager.

    update(self, _iteration: int) -> None:
        Update the state of the DataManager.

    _choose_opening(self) -> None:
        Choose the opening strategy for the bot based on the opponent's previous game.

    _get_build_cycle(self) -> List[str]:
        Get the list of available build strategies for the bot.

    _get_opponent_data(self, _opponent_id: str) -> None:
        Load the opponent's match history from a json file.

    store_opponent_data(self, result: Union[Result, str]) -> None:
        Save the result of the current match to the opponent's match history.
    """

    def __init__(self, ai, config: Dict, mediator: ManagerMediator) -> None:
        super().__init__(ai, config, mediator)
        self.manager_requests_dict = {
            ManagerRequestType.GET_CHOSEN_OPENING: lambda kwargs: self.chosen_opening
        }
        self.chosen_opening: str = ""
        self.build_cycle: list = self._get_build_cycle()
        self.found_build: bool = False
        self.opponent_history: list = []

        self.file_path: path = path.join(
            DATA_DIR, f"{self.ai.opponent_id}-{self.ai.race.name.lower()}.json"
        )
        self.build_selection_method: str = CYCLE
        self.data_saved: bool = False
        # how many games to build data for winrate based selection
        self.min_games: int = 3

    def manager_request(
        self,
        receiver: ManagerName,
        request: ManagerRequestType,
        reason: str = None,
        **kwargs,
    ) -> Optional[Union[str, list[str]]]:
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

    def initialise(self) -> None:

        if BUILD_SELECTION in self.config and self.config[USE_DATA]:
            if self.config[BUILD_SELECTION] == WINRATE_BASED:
                self.build_selection_method = WINRATE_BASED
        if MIN_GAMES_WINRATE_BASED in self.config:
            self.min_games = self.config[MIN_GAMES_WINRATE_BASED]

        if BUILD_CHOICES in self.config:
            if self.config[USE_DATA]:
                self._get_opponent_data(self.ai.opponent_id)
                self._choose_opening()

            else:
                self.chosen_opening = self.build_cycle[0]

    async def update(self, _iteration: int) -> None:
        """Not used by this manager.

        Manager is an abstract class and must have an ``update`` method.

        Parameters
        ----------
        _iteration :
            The current game iteration
        """
        pass

    def _choose_opening(self) -> None:
        """
        Improved: Pick the build with the highest winrate over its last 10 games.
        Fallback: Use previous cycling logic if insufficient data or all winrates are 0.
        """

        if self.build_selection_method == WINRATE_BASED:
            # Prepare data
            build_games = defaultdict(deque)  # build -> deque of last 10 results
            for entry in reversed(self.opponent_history):
                build = entry.get(STRATEGY_USED)
                result = entry.get(RESULT)
                if build in self.build_cycle:
                    dq = build_games[build]
                    if len(dq) < 10:
                        dq.appendleft(result)
                    else:
                        continue

            # Compute winrates only for builds with at least MIN_GAMES
            winrates = {}
            for build in self.build_cycle:
                games = build_games.get(build, [])
                if len(games) >= self.min_games:
                    wins = sum(1 for r in games if r == 2)
                    winrates[build] = wins / len(games)
                else:
                    winrates[build] = -1  # Not enough data

            # Select best build (prefer most recent in cycle)
            best_build = None
            best_winrate = -1
            for build in reversed(self.build_cycle):
                logger.info(f"{build}: {winrates[build]}")
                if winrates[build] > best_winrate:
                    best_winrate = winrates[build]
                    best_build = build

            # Use best build if there is enough data and winrate > 0
            if best_build is not None and winrates[best_build] > 0:
                self.chosen_opening = best_build
                logger.info(f"Using {best_build} with a winrate of {best_winrate}")
                return

            logger.info("Not enough opening data, using cycle logic")

        # default CYCLE method, also used if not enough data present
        last_build: str = self.opponent_history[-1][STRATEGY_USED]
        last_result: int = self.opponent_history[-1][RESULT]
        self.found_build = False
        for i, build in enumerate(self.build_cycle):
            if last_build == build:
                self.found_build = True
                # Defeat
                if last_result == 0:
                    index: int = 0 if len(self.build_cycle) <= i + 1 else i + 1
                    self.chosen_opening = self.build_cycle[index]
                else:
                    self.chosen_opening = build
                break
        # incase build from last game wasn't found in build cycle
        if not self.found_build:
            self.chosen_opening = self.build_cycle[0]

    def _get_build_cycle(self) -> List[str]:
        if self.config[DEBUG]:
            opponent_id: str = TEST_OPPONENT_ID
        else:
            opponent_id: str = self.ai.opponent_id

        build_cycle: List[str] = []
        if BUILD_CHOICES in self.config:
            # get a build cycle from config depending on ai arena opponent id
            if opponent_id in self.config[BUILD_CHOICES]:
                for build in self.config[BUILD_CHOICES][opponent_id][CYCLE]:
                    build_cycle.append(build)
            # else choose a cycle depending on the enemy race
            elif self.ai.enemy_race.name in self.config[BUILD_CHOICES]:
                for build in self.config[BUILD_CHOICES][self.ai.enemy_race.name][CYCLE]:
                    build_cycle.append(build)

        return build_cycle

    def _get_opponent_data(self, _opponent_id: str) -> None:
        if path.isfile(self.file_path):
            with open(self.file_path, "r") as f:
                self.opponent_history = json.load(f)
        else:
            # no data, create a dummy version
            self.opponent_history = [
                {
                    RACE: str(self.ai.enemy_race),
                    DURATION: 0,
                    STRATEGY_USED: self.build_cycle[0],
                    RESULT: 2,
                }
            ]

    def store_opponent_data(self, result: Union[Result, str]) -> None:
        # only write results once
        if self.data_saved:
            return
        if not isinstance(result, str):
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

        self.add_game_to_dict(self.chosen_opening, int(self.ai.time), result_id)
        os.makedirs("data", exist_ok=True)
        with open(self.file_path, "w") as f:
            json.dump(self.opponent_history, f)
        self.data_saved = True

    def add_game_to_dict(self, bot_mode: str, game_duration: int, result: int) -> None:
        game = {
            RACE: str(self.ai.enemy_race),
            DURATION: game_duration,
            STRATEGY_USED: bot_mode,
            RESULT: result,
        }
        self.opponent_history.append(game)
