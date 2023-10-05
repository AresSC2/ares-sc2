from pathlib import Path

import pytest
from sc2.ids.ability_id import AbilityId

from ares import AresBot
from ares.dicts.ability_cooldowns import ABILITY_FRAME_COOL_DOWN

pytest_plugins = ("pytest_asyncio",)

MAPS: list[Path] = [
    map_path
    for map_path in (Path(__file__).parent / "pickle_data").iterdir()
    if map_path.suffix == ".xz"
]


@pytest.mark.parametrize("bot", MAPS, indirect=True)
class TestMediator:
    scenarios = [(map_path.name, {"map_path": map_path}) for map_path in MAPS]

    @pytest.mark.asyncio
    async def test_update_ability_tracker(self, bot: AresBot, event_loop):
        # arrange
        ability: AbilityId = AbilityId.WIDOWMINEATTACK_WIDOWMINEATTACK
        current_frame: int = bot.state.game_loop
        unit_tag: int = 123458
        # hacky way to get out tag in the ability tracker bookkeeping
        bot.manager_hub.ability_tracker_manager.unit_to_ability_dict[unit_tag] = {}
        # act
        bot.mediator.update_unit_to_ability_dict(
            ability=ability,
            unit_tag=unit_tag,
        )
        # assert
        unit_to_ability_dict: dict[
            int, dict[AbilityId, int]
        ] = bot.mediator.get_unit_to_ability_dict

        # unit present in ability tracker
        assert unit_tag in unit_to_ability_dict
        # ability is associated with this unit
        assert ability in unit_to_ability_dict[unit_tag]
        # frame ability is ready again is correct
        assert (
            unit_to_ability_dict[unit_tag][ability]
            == current_frame + ABILITY_FRAME_COOL_DOWN[ability]
        )
