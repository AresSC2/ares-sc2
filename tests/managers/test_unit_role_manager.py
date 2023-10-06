from pathlib import Path

import pytest
from sc2.unit import Unit

from ares import AresBot
from ares.consts import UnitRole
from ares.managers.unit_role_manager import UnitRoleManager

pytest_plugins = ("pytest_asyncio",)

MAPS: list[Path] = [
    map_path
    for map_path in (Path(__file__).parent.parent / "pickle_data").iterdir()
    if map_path.suffix == ".xz"
]


@pytest.mark.parametrize("bot", MAPS, indirect=True)
class TestUnitRoleManager:
    scenarios = [(map_path.name, {"map_path": map_path}) for map_path in MAPS]

    def test_assign_role(self, bot: AresBot, event_loop):
        # arrange
        unit_role_manager: UnitRoleManager = bot.manager_hub.unit_role_manager
        worker: Unit = bot.workers[0]

        # act
        unit_role_manager.assign_role(worker.tag, UnitRole.DEFENDING)

        # assert
        assert worker.tag in unit_role_manager.unit_role_dict[UnitRole.DEFENDING]

    def test_batch_assign_role(self, bot: AresBot, event_loop):
        # arrange
        unit_role_manager: UnitRoleManager = bot.manager_hub.unit_role_manager
        tags: set[int] = bot.workers.tags

        # act
        unit_role_manager.batch_assign_role(tags, UnitRole.DEFENDING)

        # assert
        for tag in tags:
            assert tag in unit_role_manager.unit_role_dict[UnitRole.DEFENDING]

    def test_clear_role(self, bot: AresBot, event_loop):
        # arrange
        unit_role_manager: UnitRoleManager = bot.manager_hub.unit_role_manager
        tag: int = bot.workers[0].tag

        # act
        unit_role_manager.assign_role(tag, UnitRole.DEFENDING)
        unit_role_manager.clear_role(tag)

        # assert
        unit_role_dict = unit_role_manager.unit_role_dict
        for role in unit_role_dict:
            assert tag not in unit_role_dict[role]

    def test_batch_clear_role(self, bot: AresBot, event_loop):
        # arrange
        unit_role_manager: UnitRoleManager = bot.manager_hub.unit_role_manager
        tags: set[int] = bot.workers.tags

        # act
        unit_role_manager.batch_assign_role(tags, UnitRole.DEFENDING)
        unit_role_manager.batch_clear_role(tags)

        # assert
        unit_role_dict = unit_role_manager.unit_role_dict
        for tag in tags:
            for role in unit_role_dict:
                assert tag not in unit_role_dict[role]
