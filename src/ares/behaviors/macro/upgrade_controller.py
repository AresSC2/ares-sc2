from dataclasses import dataclass
from typing import TYPE_CHECKING

from loguru import logger
from sc2.data import Race
from sc2.dicts.unit_research_abilities import RESEARCH_INFO
from sc2.dicts.upgrade_researched_from import UPGRADE_RESEARCHED_FROM
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId as UnitID
from sc2.ids.upgrade_id import UpgradeId
from sc2.position import Point2
from sc2.unit import Unit

from ares.behaviors.macro.tech_up import TechUp

if TYPE_CHECKING:
    from ares import AresBot

from ares.behaviors.macro.macro_behavior import MacroBehavior
from ares.managers.manager_mediator import ManagerMediator


@dataclass
class UpgradeController(MacroBehavior):
    """Research upgrades, if the upgrade is not
    currently researchable this behavior will automatically
    make the tech buildings required.


    Example:
    ```py
    from ares.behaviors.macro import UpgradeController
    from sc2.ids.upgrade_id import UpgradeId

    desired_upgrades: list[UpgradeId] = [
        UpgradeId.TERRANINFANTRYWEAPONSLEVEL1,
        UpgradeId.TERRANINFANTRYWEAPONSLEVEL2,
        UpgradeId.BANSHEECLOAK,
        UpgradeId.PERSONALCLOAKING
    ]

    self.register_behavior(
        UpgradeController(desired_upgrades, base_location=self.start_location)
    )
    ```

    Attributes
    ----------
    upgrade_list : list[UpgradeId]
        List of desired upgrades.
    base_location : Point2
        Where to build upgrade buildings.

    Returns
    ----------
    bool :
        True if this Behavior carried out an action.
    """

    upgrade_list: list[UpgradeId]
    base_location: Point2

    def execute(self, ai: "AresBot", config: dict, mediator: ManagerMediator) -> bool:
        for upgrade in self.upgrade_list:
            if ai.pending_or_complete_upgrade(upgrade):
                continue

            researched_from_id: UnitID = UPGRADE_RESEARCHED_FROM[upgrade]
            researched_from: list[Unit] = [
                s for s in mediator.get_own_structures_dict[researched_from_id]
            ]

            # there is nowhere to research this from, tech up to it
            if not researched_from:
                teching: bool = TechUp(
                    desired_tech=upgrade, base_location=self.base_location
                ).execute(ai, config, mediator)
                # we've carried out an action, return True
                if teching:
                    return True

            # we have somewhere to research from, if it's possible
            # carry out the action
            else:
                idle: list[Unit] = [
                    s
                    for s in researched_from
                    if s.is_ready
                    and s.is_idle
                    and (not ai.race == Race.Protoss or s.is_powered)
                ]
                if idle and ai.can_afford(upgrade):
                    building: Unit = idle[0]
                    research_info: dict = RESEARCH_INFO[researched_from_id][upgrade]
                    ability: AbilityId = research_info["ability"]
                    if ability in building.abilities:
                        building.research(upgrade)
                        logger.info(f"{ai.time_formatted}: Researching {upgrade}")
                        return True
                    # there is a structure to upgrade from, but:
                    # we can't do the upgrade, might need something like:
                    # hive for 3/3? twilight council for 2/2?
                    elif required_building := research_info.get(
                        "required_building", None
                    ):
                        return TechUp(
                            desired_tech=required_building,
                            base_location=self.base_location,
                        ).execute(ai, config, mediator)

        # found nothing to do
        return False
