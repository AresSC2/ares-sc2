from pathlib import Path

import pytest

from ares import AresBot
from ares.consts import RESULT, STRATEGY_USED, WINRATE_BASED
from ares.managers.data_manager import DataManager

pytest_plugins = ("pytest_asyncio",)

MAPS: list[Path] = [
    map_path
    for map_path in (Path(__file__).parent.parent / "pickle_data").iterdir()
    if map_path.suffix == ".xz"
]


@pytest.mark.parametrize("bot", MAPS, indirect=True)
class TestDataManager:
    scenarios = [(map_path.name, {"map_path": map_path}) for map_path in MAPS]

    def test_choose_opening_low_data(self, bot: AresBot, event_loop):
        dm: DataManager = bot.manager_hub.data_manager
        dm.build_selection_method = WINRATE_BASED
        dm.build_cycle = ["A", "B", "C"]
        dm.opponent_history = [
            {STRATEGY_USED: "A", RESULT: 0},
            {STRATEGY_USED: "B", RESULT: 2},
            {STRATEGY_USED: "B", RESULT: 0},
        ]
        dm._choose_opening()
        assert dm.chosen_opening == "C"

    def test_choose_opening_all_losses(self, bot: AresBot, event_loop):
        dm: DataManager = bot.manager_hub.data_manager
        dm.build_selection_method = WINRATE_BASED
        dm.build_cycle = ["A", "B", "C"]
        dm.opponent_history = [
            {STRATEGY_USED: "A", RESULT: 0},
            {STRATEGY_USED: "B", RESULT: 0},
            {STRATEGY_USED: "C", RESULT: 0},
            {STRATEGY_USED: "A", RESULT: 0},
            {STRATEGY_USED: "B", RESULT: 0},
            {STRATEGY_USED: "C", RESULT: 0},
            {STRATEGY_USED: "A", RESULT: 0},
            {STRATEGY_USED: "B", RESULT: 0},
            {STRATEGY_USED: "C", RESULT: 0},
        ]
        dm._choose_opening()
        assert dm.chosen_opening == "A"  # Fallback

    def test_choose_opening_winrate(self, bot: AresBot, event_loop):
        dm: DataManager = bot.manager_hub.data_manager
        dm.build_selection_method = WINRATE_BASED
        dm.build_cycle = ["A", "B", "C"]
        dm.opponent_history = [
            {STRATEGY_USED: "A", RESULT: 2},
            {STRATEGY_USED: "A", RESULT: 0},
            {STRATEGY_USED: "A", RESULT: 2},
            {STRATEGY_USED: "B", RESULT: 0},
            {STRATEGY_USED: "B", RESULT: 0},
            {STRATEGY_USED: "B", RESULT: 0},
            {STRATEGY_USED: "C", RESULT: 0},
            {STRATEGY_USED: "C", RESULT: 0},
            {STRATEGY_USED: "C", RESULT: 0},
        ]
        dm._choose_opening()
        assert dm.chosen_opening == "A"  # Only A has winrate > 0

    def test_choose_opening_tie(self, bot: AresBot, event_loop):

        dm: DataManager = bot.manager_hub.data_manager
        dm.build_selection_method = WINRATE_BASED
        dm.build_cycle = ["A", "B", "C"]
        dm.opponent_history = [
            {STRATEGY_USED: "A", RESULT: 0},
            {STRATEGY_USED: "A", RESULT: 0},
            {STRATEGY_USED: "A", RESULT: 0},
            {STRATEGY_USED: "B", RESULT: 0},
            {STRATEGY_USED: "B", RESULT: 0},
            {STRATEGY_USED: "B", RESULT: 0},
            {STRATEGY_USED: "C", RESULT: 0},
            {STRATEGY_USED: "C", RESULT: 0},
            {STRATEGY_USED: "C", RESULT: 0},
        ]
        dm._choose_opening()
        # All builds have tied winrates
        # last result was a loss for C, so should cycle to A
        assert dm.chosen_opening == "A"

        # add this loss to history
        dm.opponent_history.append({STRATEGY_USED: "A", RESULT: 0})
        # now should cycle to B
        dm._choose_opening()
        assert dm.chosen_opening == "B"

        # same idea, just adding a few more to ensure it works
        dm.opponent_history.append({STRATEGY_USED: "B", RESULT: 0})
        dm._choose_opening()
        assert dm.chosen_opening == "C"
        dm.opponent_history.append({STRATEGY_USED: "C", RESULT: 0})
        dm._choose_opening()
        assert dm.chosen_opening == "A"
        dm.opponent_history.append({STRATEGY_USED: "A", RESULT: 0})
        dm._choose_opening()
        assert dm.chosen_opening == "B"

    def test_choose_opening_large_history(self, bot: AresBot, event_loop):
        dm: DataManager = bot.manager_hub.data_manager
        dm.build_selection_method = WINRATE_BASED
        dm.build_cycle = ["A", "B", "C"]

        # Build "A": 25 games, last 10 are all losses (winrate 0.0 in last 10)
        history_A = [{STRATEGY_USED: "A", RESULT: 2}] * 15 + [
            {STRATEGY_USED: "A", RESULT: 0}
        ] * 10

        # Build "B": 25 games, last 10 are all wins (winrate 1.0 in last 10)
        history_B = [{STRATEGY_USED: "B", RESULT: 0}] * 15 + [
            {STRATEGY_USED: "B", RESULT: 2}
        ] * 10

        # Build "C": 25 games, last 10 are mixed
        # (5 wins, 5 losses, winrate 0.5 in last 10)
        history_C = [{STRATEGY_USED: "C", RESULT: 0}] * 15 + [
            {STRATEGY_USED: "C", RESULT: 2},
            {STRATEGY_USED: "C", RESULT: 0},
        ] * 5

        # Interleave histories to simulate real play order
        dm.opponent_history = []
        for i in range(25):
            dm.opponent_history.append(history_A[i])
            dm.opponent_history.append(history_B[i])
            dm.opponent_history.append(history_C[i])

        dm._choose_opening()
        # B has the highest winrate (1.0) in its last 10 games
        assert dm.chosen_opening == "B"

        # check that we switch to "C" after 5 losses
        for i in range(5):
            history_B = {STRATEGY_USED: "B", RESULT: 0}
            dm.opponent_history.append(history_B)
            dm._choose_opening()
            if i < 4:
                assert dm.chosen_opening == "B"
            else:
                assert dm.chosen_opening == "C"

    def test_winrate_logic_requires_min_games(self, bot: AresBot, event_loop):
        dm: DataManager = bot.manager_hub.data_manager
        dm.build_selection_method = WINRATE_BASED
        dm.build_cycle = ["A", "B", "C"]
        dm.min_games = 3
        # Only build A has enough games, B and C do not
        dm.opponent_history = [
            {STRATEGY_USED: "A", RESULT: 2},
            {STRATEGY_USED: "A", RESULT: 0},
            {STRATEGY_USED: "A", RESULT: 2},
            {STRATEGY_USED: "B", RESULT: 0},
            {STRATEGY_USED: "C", RESULT: 0},
        ]
        # Should fallback to cycle logic, i.e., pick next after last used
        dm._choose_opening()
        # The fallback cycle logic should pick the next build after the last one played
        # In this case, last played is C with a defeat, so next should be A
        assert dm.chosen_opening == "A"
