from pathlib import Path

import pytest
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId as UnitID
from sc2.unit import Unit

from ares import AresBot
from ares.consts import LOSS_EMPHATIC_OR_WORSE, VICTORY_EMPHATIC_OR_BETTER
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
    async def test_get_ability_tracker(self, bot: AresBot, event_loop):
        # arrange
        ability: AbilityId = AbilityId.WIDOWMINEATTACK_WIDOWMINEATTACK
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

    @pytest.mark.asyncio
    async def test_build_with_specific_worker(self, bot: AresBot, event_loop):
        # arrange
        worker: Unit = bot.workers[0]
        # act
        bot.mediator.build_with_specific_worker(
            worker=worker,
            structure_type=UnitID.SPAWNINGPOOL,
            pos=bot.game_info.map_center,
        )
        # assert
        building_tracker: dict = bot.mediator.get_building_tracker_dict
        assert worker.tag in building_tracker
        assert building_tracker[worker.tag]["id"] == UnitID.SPAWNINGPOOL

    def test_can_win_fight(self, bot: AresBot, event_loop):
        # arrange
        # easy fight
        army = bot.units
        enemy = bot.enemy_units[:3]
        # act
        result = bot.mediator.can_win_fight(own_units=army, enemy_units=enemy)
        # assert
        assert result in VICTORY_EMPHATIC_OR_BETTER

        # arrange
        # hard fight
        army = bot.units[:3]
        enemy = bot.enemy_units
        # act
        result = bot.mediator.can_win_fight(own_units=army, enemy_units=enemy)
        # assert
        assert result in LOSS_EMPHATIC_OR_WORSE

    def test_enemy_expanded(self, bot: AresBot, event_loop):
        assert not bot.mediator.get_enemy_expanded

    def test_cheese(self, bot: AresBot, event_loop):
        assert not bot.mediator.get_enemy_ling_rushed
        assert not bot.mediator.get_enemy_marine_rush
        assert not bot.mediator.get_enemy_marauder_rush
        assert not bot.mediator.get_enemy_four_gate
        assert not bot.mediator.get_enemy_ravager_rush

    def test_can_retrieve_all_grids(self, bot: AresBot, event_loop):
        # arrange
        # act
        air_avoidance_grid = bot.mediator.get_air_avoidance_grid
        air_grid = bot.mediator.get_air_grid
        air_vs_ground_grid = bot.mediator.get_air_vs_ground_grid
        cached_ground_grid = bot.mediator.get_cached_ground_grid
        ground_grid = bot.mediator.get_ground_grid
        climber = bot.mediator.get_climber_grid
        ground_avoidance_grid = bot.mediator.get_ground_avoidance_grid
        ground_to_air_grid = bot.mediator.get_ground_to_air_grid
        priority_ground_avoidance_grid = bot.mediator.get_priority_ground_avoidance_grid
        # assert
        assert air_avoidance_grid is not None
        assert air_grid is not None
        assert air_vs_ground_grid is not None
        assert cached_ground_grid is not None
        assert ground_grid is not None
        assert climber is not None
        assert ground_avoidance_grid is not None
        assert ground_to_air_grid is not None
        assert priority_ground_avoidance_grid is not None
        # also check each grid is the correct shape
        assert air_avoidance_grid.shape == (
            bot.game_info.pathing_grid.width,
            bot.game_info.pathing_grid.height,
        )
        assert air_grid.shape == (
            bot.game_info.pathing_grid.width,
            bot.game_info.pathing_grid.height,
        )
        assert air_vs_ground_grid.shape == (
            bot.game_info.pathing_grid.width,
            bot.game_info.pathing_grid.height,
        )
        assert cached_ground_grid.shape == (
            bot.game_info.pathing_grid.width,
            bot.game_info.pathing_grid.height,
        )
        assert ground_grid.shape == (
            bot.game_info.pathing_grid.width,
            bot.game_info.pathing_grid.height,
        )
        assert climber.shape == (
            bot.game_info.pathing_grid.width,
            bot.game_info.pathing_grid.height,
        )
        assert ground_avoidance_grid.shape == (
            bot.game_info.pathing_grid.width,
            bot.game_info.pathing_grid.height,
        )
        assert ground_to_air_grid.shape == (
            bot.game_info.pathing_grid.width,
            bot.game_info.pathing_grid.height,
        )
        assert priority_ground_avoidance_grid.shape == (
            bot.game_info.pathing_grid.width,
            bot.game_info.pathing_grid.height,
        )
