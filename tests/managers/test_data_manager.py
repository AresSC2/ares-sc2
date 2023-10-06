from pathlib import Path

import pytest

from ares import AresBot

pytest_plugins = ("pytest_asyncio",)

MAPS: list[Path] = [
    map_path
    for map_path in (Path(__file__).parent.parent / "pickle_data").iterdir()
    if map_path.suffix == ".xz"
]


@pytest.mark.parametrize("bot", MAPS, indirect=True)
class TestDataManager:
    scenarios = [(map_path.name, {"map_path": map_path}) for map_path in MAPS]

    def test_chosen_opening(self, bot: AresBot, event_loop):
        """
        Dummy test for now
        """
        assert bot.manager_hub.data_manager.chosen_opening == ""
