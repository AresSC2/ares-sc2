from pathlib import Path

import pytest
from sc2.ids.ability_id import AbilityId

from ares import AresBot
from ares.dicts.ability_cooldowns import ABILITY_FRAME_COOL_DOWN
from tests.load_bot_from_pickle import build_bot_object_from_pickle_data

pytest_plugins = ("pytest_asyncio",)

MAPS: list[Path] = [
    map_path
    for map_path in (Path(__file__).parent / "pickle_data").iterdir()
    if map_path.suffix == ".xz"
]


def pytest_generate_tests(metafunc):
    idlist = []
    argvalues = []
    for scenario in metafunc.cls.scenarios:
        idlist.append(scenario[0])
        items = scenario[1].items()
        argnames = [x[0] for x in items]
        argvalues.append(([x[1] for x in items]))
    metafunc.parametrize(argnames, argvalues, ids=idlist, scope="class")


class TestMediator:
    scenarios = [(map_path.name, {"map_path": map_path}) for map_path in MAPS]

    @pytest.mark.asyncio
    async def test_update_ability_tracker(self, map_path: Path):
        # arrange
        ability: AbilityId = AbilityId.WIDOWMINEATTACK_WIDOWMINEATTACK
        bot: AresBot = await build_bot_object_from_pickle_data(map_path)
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
