from pathlib import Path

import pytest
from sc2.unit import Unit

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

    def test_available_minerals(self, bot: AresBot, event_loop):
        """
        We know ares only finds mfs at townhalls
        Since pickled data only has one townhall
        We know this should equal 8
        """
        # arrange
        resource_manager: ResourceManager = bot.manager_hub.resource_manager
        num_valid_min_fields: int = 8

        # act
        num_mfs: int = len(resource_manager.available_minerals)

        # assert
        assert num_valid_min_fields == num_mfs

    def test_remove_worker_from_mineral(self, bot: AresBot, event_loop):
        """ """
        # arrange
        resource_manager: ResourceManager = bot.manager_hub.resource_manager
        num_workers_assigned: int = len(resource_manager.worker_to_mineral_patch_dict)
        for tag in resource_manager.worker_to_mineral_patch_dict:
            worker: Unit = bot.unit_tag_dict[tag]
            break

        # act
        resource_manager.remove_worker_from_mineral(worker.tag)

        # assert
        new_num_workers_assigned: int = len(
            resource_manager.worker_to_mineral_patch_dict
        )
        assert new_num_workers_assigned == num_workers_assigned - 1
        assert worker.tag not in resource_manager.worker_to_mineral_patch_dict
        assert worker.tag not in resource_manager.worker_tag_to_townhall_tag
