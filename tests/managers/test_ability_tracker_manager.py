from pathlib import Path

import pytest
from sc2.ids.ability_id import AbilityId

from ares import AresBot
from ares.dicts.ability_cooldowns import ABILITY_FRAME_COOL_DOWN
from ares.managers.ability_tracker_manager import AbilityTrackerManager

pytest_plugins = ("pytest_asyncio",)

MAPS: list[Path] = [
    map_path
    for map_path in (Path(__file__).parent.parent / "pickle_data").iterdir()
    if map_path.suffix == ".xz"
]


@pytest.mark.parametrize("bot", MAPS, indirect=True)
class TestAbilityTrackerManager:
    def test_update_ability_tracker(self, bot: AresBot, event_loop):
        # arrange
        ability: AbilityId = AbilityId.WIDOWMINEATTACK_WIDOWMINEATTACK
        # bot: AresBot = await build_bot_object_from_pickle_data(map_path)
        ability_tracker_manager: AbilityTrackerManager = AbilityTrackerManager(
            bot, bot.config, bot.mediator
        )

        current_frame: int = bot.state.game_loop
        unit_tag: int = 123458
        # hacky way to get out tag in the ability tracker bookkeeping
        ability_tracker_manager.unit_to_ability_dict[unit_tag] = {}
        # act
        ability_tracker_manager.update_unit_to_ability_dict(
            ability=ability,
            unit_tag=unit_tag,
        )
        # assert
        unit_to_ability_dict: dict[
            int, dict[AbilityId, int]
        ] = ability_tracker_manager.unit_to_ability_dict

        # unit present in ability tracker
        assert unit_tag in unit_to_ability_dict
        # ability is associated with this unit
        assert ability in unit_to_ability_dict[unit_tag]
        # frame ability is ready again is correct
        assert (
            unit_to_ability_dict[unit_tag][ability]
            == current_frame + ABILITY_FRAME_COOL_DOWN[ability]
        )
