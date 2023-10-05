from pathlib import Path

import pytest

from ares import AresBot
from ares.managers.resource_manager import ResourceManager

pytest_plugins = ("pytest_asyncio",)

MAPS: list[Path] = [
    map_path
    for map_path in (Path(__file__).parent.parent / "pickle_data").iterdir()
    if map_path.suffix == ".xz"
]


@pytest.mark.parametrize("bot", MAPS, indirect=True)
class TestResourceManager:
    scenarios = [(map_path.name, {"map_path": map_path}) for map_path in MAPS]

    def test_set_workers_per_gas(self, bot: AresBot, event_loop):
        """
        Dummy test for now
        """
        # arrange
        resource_manager: ResourceManager = bot.manager_hub.resource_manager
        num_per_gas: int = 3

        # act
        resource_manager.set_worker_per_gas(num_per_gas)

        # assert
        assert resource_manager.workers_per_gas == num_per_gas
