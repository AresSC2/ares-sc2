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
class TestIntelManager:
    scenarios = [(map_path.name, {"map_path": map_path}) for map_path in MAPS]

    def test_enemy_has_base_outside_natural(self, bot: AresBot, event_loop):
        assert not bot.manager_hub.intel_manager.get_enemy_has_base_outside_natural

    def test_no_enemy_cheese(self, bot: AresBot, event_loop):
        """
        TODO: Test the opposite of these
            Probably need pickled map data with enemy spawned
            where it looks like cheese.
        """
        intel_manager = bot.manager_hub.intel_manager
        assert not intel_manager.get_enemy_marauder_rush
        assert not intel_manager.enemy_ling_rushed
        assert not intel_manager.get_enemy_four_gate
        assert not intel_manager.get_enemy_marine_rush
        assert not intel_manager.get_enemy_was_greedy
        assert not intel_manager.get_enemy_ravager_rush
        assert not intel_manager.is_proxy_zealot
