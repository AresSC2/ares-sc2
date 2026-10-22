from __future__ import annotations

from collections import defaultdict
from unittest.mock import MagicMock, patch

from sc2.data import Race
from sc2.dicts.unit_research_abilities import RESEARCH_INFO
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId
from sc2.position import Point2

from ares.behaviors.macro import UpgradeController
from ares.custom_bot_ai import CustomBotAI

TECH_UP_PATH: str = "ares.behaviors.macro.upgrade_controller.TechUp"


def _research_structure(researched_from: UnitTypeId, upgrade: UpgradeId) -> MagicMock:
    """An idle, ready structure that is able to research `upgrade`."""
    structure = MagicMock(name=f"{researched_from.name}_structure")
    structure.is_ready = True
    structure.is_idle = True
    structure.abilities = {RESEARCH_INFO[researched_from][upgrade]["ability"]}
    return structure


def _setup(structures: dict[UnitTypeId, list]) -> tuple[MagicMock, MagicMock]:
    ai = MagicMock()
    ai.race = Race.Zerg
    ai.pending_or_complete_upgrade.return_value = False
    ai.can_afford.return_value = True

    mediator = MagicMock()
    mediator.get_own_structures_dict = defaultdict(list, structures)
    return ai, mediator


class TestUpgradeController:
    def test_researches_hatchery_upgrade_from_lair(self):
        # arrange: no hatcheries left, they have all morphed into lairs
        lair = _research_structure(UnitTypeId.HATCHERY, UpgradeId.OVERLORDSPEED)
        ai, mediator = _setup({UnitTypeId.LAIR: [lair]})

        # act
        with patch(TECH_UP_PATH) as tech_up:
            did_action: bool = UpgradeController(
                [UpgradeId.OVERLORDSPEED], base_location=Point2((0, 0))
            ).execute(ai, {}, mediator)

        # assert: research from lair, rather than teching to a new hatchery
        assert did_action
        lair.research.assert_called_once_with(UpgradeId.OVERLORDSPEED)
        tech_up.assert_not_called()

    def test_researches_spire_upgrade_from_greater_spire(self):
        # arrange
        greater_spire = _research_structure(
            UnitTypeId.SPIRE, UpgradeId.ZERGFLYERWEAPONSLEVEL1
        )
        ai, mediator = _setup({UnitTypeId.GREATERSPIRE: [greater_spire]})

        # act
        with patch(TECH_UP_PATH) as tech_up:
            did_action: bool = UpgradeController(
                [UpgradeId.ZERGFLYERWEAPONSLEVEL1], base_location=Point2((0, 0))
            ).execute(ai, {}, mediator)

        # assert
        assert did_action
        greater_spire.research.assert_called_once_with(UpgradeId.ZERGFLYERWEAPONSLEVEL1)
        tech_up.assert_not_called()

    def test_auto_tech_up_disabled_checks_remaining_upgrades(self):
        # arrange: no spawning pool for ling speed, but overlord speed is available
        hatchery = _research_structure(UnitTypeId.HATCHERY, UpgradeId.OVERLORDSPEED)
        ai, mediator = _setup({UnitTypeId.HATCHERY: [hatchery]})

        # act
        did_action: bool = UpgradeController(
            [UpgradeId.ZERGLINGMOVEMENTSPEED, UpgradeId.OVERLORDSPEED],
            base_location=Point2((0, 0)),
            auto_tech_up_enabled=False,
        ).execute(ai, {}, mediator)

        # assert
        assert did_action
        hatchery.research.assert_called_once_with(UpgradeId.OVERLORDSPEED)

    def test_failed_required_building_tech_up_checks_remaining_upgrades(self):
        # arrange: evo chamber can't research +2 armor without a lair,
        # and teching to a lair fails (ie: can't afford it)
        evo = _research_structure(
            UnitTypeId.EVOLUTIONCHAMBER, UpgradeId.ZERGGROUNDARMORSLEVEL1
        )
        hatchery = _research_structure(UnitTypeId.HATCHERY, UpgradeId.OVERLORDSPEED)
        ai, mediator = _setup(
            {
                UnitTypeId.EVOLUTIONCHAMBER: [evo],
                UnitTypeId.HATCHERY: [hatchery],
            }
        )

        # act
        with patch(TECH_UP_PATH) as tech_up:
            tech_up.return_value.execute.return_value = False
            did_action: bool = UpgradeController(
                [UpgradeId.ZERGGROUNDARMORSLEVEL2, UpgradeId.OVERLORDSPEED],
                base_location=Point2((0, 0)),
            ).execute(ai, {}, mediator)

        # assert
        assert did_action
        tech_up.assert_called_once_with(
            desired_tech=UnitTypeId.LAIR, base_location=Point2((0, 0))
        )
        evo.research.assert_not_called()
        hatchery.research.assert_called_once_with(UpgradeId.OVERLORDSPEED)


def test_pending_upgrade_found_in_morphed_structure():
    # arrange: overlord speed is researching in a lair, no hatcheries exist
    ability = RESEARCH_INFO[UnitTypeId.HATCHERY][UpgradeId.OVERLORDSPEED]["ability"]
    order = MagicMock()
    order.ability.exact_id = ability
    lair = MagicMock()
    lair.orders = [order]

    bot = MagicMock()
    bot.state.upgrades = set()
    bot.game_data.upgrades[
        UpgradeId.OVERLORDSPEED.value
    ].research_ability.exact_id = ability
    bot.mediator.get_own_structures_dict = defaultdict(list, {UnitTypeId.LAIR: [lair]})

    # act / assert
    assert CustomBotAI.pending_or_complete_upgrade(bot, UpgradeId.OVERLORDSPEED)
