from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

from loguru import logger
from sc2.dicts.unit_trained_from import UNIT_TRAINED_FROM
from sc2.dicts.upgrade_researched_from import UPGRADE_RESEARCHED_FROM
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId as UnitID
from sc2.ids.upgrade_id import UpgradeId
from sc2.position import Point2
from sc2.unit import Unit

from ares.behaviors.macro import BuildStructure, MacroBehavior
from ares.consts import ALL_STRUCTURES, GATEWAY_UNITS, TECHLAB_TYPES
from ares.dicts.unit_tech_requirement import UNIT_TECH_REQUIREMENT
from ares.managers.manager_mediator import ManagerMediator

if TYPE_CHECKING:
    from ares import AresBot

BUILD_TECHLAB_FROM: dict[UnitID:UnitID] = {
    UnitID.BARRACKSTECHLAB: UnitID.BARRACKS,
    UnitID.FACTORYTECHLAB: UnitID.FACTORY,
    UnitID.STARPORTTECHLAB: UnitID.STARPORT,
}


@dataclass
class TechUp(MacroBehavior):
    """Automatically tech up so desired upgrade/unit can be built.

    Example:
    ```py
    from ares.behaviors.macro import TechUp
    from sc2.ids.upgrade_id import UpgradeId

    self.register_behavior(
        TechUp(UpgradeId.BANSHEECLOAK, base_location=self.start_location)
    )
    ```

    Attributes:
        desired_tech: The desired upgrade or unit type.
        base_location: The main building location to make tech.
        ignore_existing_techlabs: If set to `True`, will
            keep building techlabs even if others exist.
            Defaults to `False`.

    """

    desired_tech: Union[UpgradeId, UnitID]
    base_location: Point2
    ignore_existing_techlabs: bool = False

    def execute(self, ai: "AresBot", config: dict, mediator: ManagerMediator) -> bool:
        assert isinstance(
            self.desired_tech, (UpgradeId, UnitID)
        ), f"Wrong type provided for `desired_tech`, got {type(self.desired_tech)}"

        # figure out where we research this unit / upgrade from
        researched_from_id: UnitID
        tech_required: list[UnitID]
        if isinstance(self.desired_tech, UpgradeId):
            researched_from_id = UPGRADE_RESEARCHED_FROM[self.desired_tech]
            tech_required = UNIT_TECH_REQUIREMENT[researched_from_id]
        else:
            if self.desired_tech in ALL_STRUCTURES:
                researched_from_id = self.desired_tech
                tech_required = UNIT_TECH_REQUIREMENT[researched_from_id]
            else:
                researched_from_id = next(iter(UNIT_TRAINED_FROM[self.desired_tech]))
                if self.desired_tech in GATEWAY_UNITS:
                    researched_from_id = UnitID.GATEWAY
                tech_required = UNIT_TECH_REQUIREMENT[self.desired_tech]

        # special handling of teching to techlabs
        if researched_from_id in TECHLAB_TYPES:
            if ai.can_afford(researched_from_id) and self._adding_techlab(
                ai,
                self.base_location,
                researched_from_id,
                tech_required,
                self.desired_tech,
                self.ignore_existing_techlabs,
            ):
                return True
            return False

        # can we build this tech building right away?
        # 1.0 = Yes, < 1.0 = No
        try:
            tech_progress: float = ai.tech_requirement_progress(researched_from_id)
        except AttributeError as e:
            logger.warning(
                f"{ai.time_formatted} Error checking tech progress for "
                f"{researched_from_id}: {e}"
            )
            return False

        # we have the tech ready to build this upgrade building right away :)
        if tech_progress == 1.0 and not ai.structure_present_or_pending(
            researched_from_id
        ):
            if researched_from_id in {UnitID.LAIR, UnitID.HIVE}:
                upgrading: bool = self._upgrade_zerg_townhall(researched_from_id, ai)
                if upgrading:
                    logger.info(
                        f"{ai.time_formatted} Adding {researched_from_id} to"
                        f" tech towards {self.desired_tech}"
                    )
                return upgrading
            # need a gateway, but we have a warpgate already
            if (
                researched_from_id == UnitID.GATEWAY
                and mediator.get_own_structures_dict[UnitID.WARPGATE]
            ):
                return False
            logger.info(
                f"{ai.time_formatted} Building {researched_from_id} "
                f"for {self.desired_tech}"
            )
            return BuildStructure(ai.start_location, researched_from_id).execute(
                ai, config, mediator
            )

        # we can't even build the upgrade building :(
        # figure out what to build to get there
        else:
            for structure_type in tech_required:
                checks: list[UnitID] = [structure_type]
                if structure_type == UnitID.GATEWAY:
                    checks.append(UnitID.WARPGATE)

                if structure_type in TECHLAB_TYPES:
                    if self._adding_techlab(
                        ai,
                        self.base_location,
                        structure_type,
                        tech_required,
                        self.desired_tech,
                        self.ignore_existing_techlabs,
                    ):
                        return True
                    continue

                if any(ai.structure_present_or_pending(check) for check in checks):
                    continue

                # found something to build?
                try:
                    tech_ready = ai.tech_requirement_progress(structure_type) == 1.0
                except AttributeError as e:
                    logger.warning(
                        f"{ai.time_formatted} Error checking tech progress "
                        f"for {structure_type}: {e}"
                    )
                    continue

                if tech_ready:
                    if structure_type in {UnitID.LAIR, UnitID.HIVE}:
                        upgrading: bool = self._upgrade_zerg_townhall(
                            structure_type, ai
                        )
                        if upgrading:
                            logger.info(
                                f"{ai.time_formatted} Adding {structure_type} to"
                                f" tech towards {self.desired_tech}"
                            )
                        return upgrading

                    building: bool = BuildStructure(
                        self.base_location, structure_type
                    ).execute(ai, ai.config, ai.mediator)
                    if building:
                        logger.info(
                            f"{ai.time_formatted} Adding {structure_type} to"
                            f" tech towards {self.desired_tech}"
                        )
                    return building

        return False

    def _adding_techlab(
        self,
        ai: "AresBot",
        base_location: Point2,
        researched_from_id: UnitID,
        tech_required: list[UnitID],
        desired_tech: Union[UnitID, UpgradeId],
        ignore_existing_techlabs: bool = False,
    ) -> bool:
        """
        ai :
        base_location :
        researched_from_id :
            The building we require
        tech_required :
            The list of tech buildings we would need to build this
        desired_tech :
            The thing we are actually trying to research / build
        """
        structures_dict: dict = ai.mediator.get_own_structures_dict
        build_techlab_from: UnitID = BUILD_TECHLAB_FROM[researched_from_id]
        _build_techlab_from_structures: list[Unit] = structures_dict[
            build_techlab_from
        ].copy()
        # looks like we already have what we are looking for?
        if (
            not ignore_existing_techlabs
            and len(
                [
                    s
                    for s in _build_techlab_from_structures
                    if s.has_techlab and s.is_idle
                ]
            )
            > 0
        ):
            return False

        # no possible way of building this techlab, tech towards it
        if not ai.structure_present_or_pending(build_techlab_from):
            for s in tech_required:
                if ai.structure_present_or_pending(s):
                    continue
                if ai.can_afford(s) and TechUp(s, base_location).execute(
                    ai, ai.config, ai.mediator
                ):
                    logger.info(
                        f"{ai.time_formatted} Adding {s} so that we can "
                        f"tech towards {desired_tech}"
                    )
                    return True
            # no point continuing
            return False

        if ai.can_afford(researched_from_id) and (
            not structures_dict[researched_from_id] or ignore_existing_techlabs
        ):
            without_techlabs: list[Unit] = [
                s
                for s in _build_techlab_from_structures
                if s.is_ready and s.is_idle and not s.has_add_on
            ]
            with_techlabs_idle: list[Unit] = [
                s for s in _build_techlab_from_structures if s.is_idle and s.has_add_on
            ]
            if without_techlabs and not with_techlabs_idle:
                without_techlabs[0].build(researched_from_id)
                logger.info(
                    f"{ai.time_formatted} Adding {researched_from_id} so that we can "
                    f"tech towards {desired_tech}. "
                    f"Ignore existing techlabs: {ignore_existing_techlabs}"
                )
                return True
        return False

    def _upgrade_zerg_townhall(self, structure_type: UnitID, ai: "AresBot") -> bool:
        structures_dict = ai.mediator.get_own_structures_dict
        if (
            not ai.can_afford(structure_type)
            or ai.already_pending(structure_type)
            or structures_dict[structure_type]
        ):
            return False

        # lair
        if (
            structure_type == UnitID.LAIR
            and not structures_dict[UnitID.HIVE]
            and (
                idle_townhalls := [
                    th for th in ai.townhalls if th.is_idle and th.is_ready
                ]
            )
        ):
            # all townhalls will be a hatchery if got to here
            th: Unit = idle_townhalls[0]
            th(AbilityId.UPGRADETOLAIR_LAIR)
            return True

        # hive
        if (
            structure_type == UnitID.HIVE
            and not structures_dict[UnitID.HIVE]
            and (
                idle_lair := [
                    th
                    for th in structures_dict[UnitID.LAIR]
                    if th.is_idle and th.is_ready
                ]
            )
        ):
            # all townhalls will be a hatchery if got to here
            th: Unit = idle_lair[0]
            th(AbilityId.UPGRADETOHIVE_HIVE)
            return True

        return False
