from dataclasses import dataclass
from typing import TYPE_CHECKING

from cython_extensions import cy_closest_to, cy_distance_to_squared
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId as UnitID
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units

from ares.behaviors.combat.individual import CombatIndividualBehavior
from ares.consts import CHANGELING_TYPES, UnitTreeQueryType
from ares.dicts.unit_data import UNIT_DATA
from ares.managers.manager_mediator import ManagerMediator

if TYPE_CHECKING:
    from ares import AresBot

STATIC_DEFENCE: set[UnitID] = {
    UnitID.BUNKER,
    UnitID.PLANETARYFORTRESS,
    UnitID.SPINECRAWLER,
    UnitID.PHOTONCANNON,
}

TANK_TYPES: set[UnitID] = {UnitID.SIEGETANKSIEGED, UnitID.SIEGETANK}


@dataclass
class SiegeTankDecision(CombatIndividualBehavior):
    """Decide if a tank should either siege or unsiege.

    VERY OPINIONATED, recommend to write own version based on this.

    Attributes:
        unit: The siege tank unit.
        close_enemy: All close by enemies.
        target: Intended destination for this tank.
        stay_sieged_near_target: This is useful for tanks in defensive position.
            If on offensive, might not be needed
            Default is False.
        remain_sieged: Sometimes we might just want to leave the tank sieged up
            Default is False.
        force_unsiege: We might want to not ever siege
            Default is False.
    """

    unit: Unit
    close_enemy: list[Unit]
    target: Point2
    stay_sieged_near_target: bool = False
    remain_sieged: bool = False
    force_unsiege: bool = False

    def execute(self, ai: "AresBot", config: dict, mediator: ManagerMediator) -> bool:
        type_id: UnitID = self.unit.type_id
        if type_id not in TANK_TYPES:
            return False

        enemy_ground: list[Unit] = [
            e
            for e in self.close_enemy
            if not e.is_burrowed
            and e.type_id not in CHANGELING_TYPES
            and not UNIT_DATA[type_id]["flying"]
        ]
        unit_pos: Point2 = self.unit.position

        if type_id == UnitID.SIEGETANK:
            if self.force_unsiege:
                return False

            # enemy are too close, don't siege no matter what
            if (
                len(
                    [
                        e
                        for e in enemy_ground
                        if cy_distance_to_squared(e.position, unit_pos) < 42.25
                    ]
                )
                > 0
            ):
                return False

            # siege up for any enemy static defence
            if (
                len(
                    [
                        e
                        for e in enemy_ground
                        if e.type_id in STATIC_DEFENCE
                        and cy_distance_to_squared(e.position, self.unit.position)
                        < 169.0
                    ]
                )
                > 0
            ):
                self.unit(AbilityId.SIEGEMODE_SIEGEMODE)
                return True
            elif (
                self.stay_sieged_near_target
                and cy_distance_to_squared(unit_pos, self.target) < 25.0
            ):
                self.unit(AbilityId.SIEGEMODE_SIEGEMODE)
                return True

            elif (
                ai.get_total_supply(enemy_ground) >= 4.0 and len(enemy_ground) > 1
            ) or ([t for t in enemy_ground if t.type_id in TANK_TYPES]):
                self.unit(AbilityId.SIEGEMODE_SIEGEMODE)
                return True

        elif type_id == UnitID.SIEGETANKSIEGED:
            if self.force_unsiege:
                self.unit(AbilityId.UNSIEGE_UNSIEGE)
                return True

            # what if we are sieged and ground enemy have got too close
            if self._enemy_too_close(unit_pos, enemy_ground):
                self.unit(AbilityId.UNSIEGE_UNSIEGE)
                return True

            # didn't actually issue an action, but nothing more needs to be done
            if self.remain_sieged or self.stay_sieged_near_target:
                return False

            # sometimes tanks get isolated a bit, which messes with close enemy calcs
            # but if there are for example marines ahead, we should stay sieged
            if self._own_units_between_tank_and_target(mediator):
                return False

            # just a general if nothing around then unsiege
            if (
                len(enemy_ground) == 0
                and cy_distance_to_squared(unit_pos, self.target) > 200.0
            ):
                self.unit(AbilityId.UNSIEGE_UNSIEGE)
                return True

        # return true for sieged up tanks, as no further action needed
        # return False for non sieged tanks
        return type_id == UnitID.SIEGETANKSIEGED

    @staticmethod
    def _enemy_too_close(unit_pos: Point2, near_enemy_ground) -> bool:
        return (
            len(
                [
                    e
                    for e in near_enemy_ground
                    if cy_distance_to_squared(e.position, unit_pos) < 16.0
                ]
            )
            > 0
            and len(
                [
                    e
                    for e in near_enemy_ground
                    if cy_distance_to_squared(e.position, unit_pos) < 144.0
                ]
            )
            < 2
        )

    def _own_units_between_tank_and_target(self, mediator: ManagerMediator):
        tank_pos: Point2 = self.unit.position
        target: Point2 = self.target

        midway_point: Point2 = Point2(
            ((tank_pos.x + target.x) / 2, (tank_pos.y + target.y) / 2)
        )

        own_units_ahead: Units = mediator.get_units_in_range(
            start_points=[midway_point],
            distances=12,
            query_tree=UnitTreeQueryType.AllOwn,
        )[0].filter(lambda u: not u.is_flying)

        if not own_units_ahead or len(own_units_ahead) < 3:
            return False

        # own units close enough?
        closest_to_tank: Unit = cy_closest_to(tank_pos, own_units_ahead)
        return cy_distance_to_squared(closest_to_tank.position, tank_pos) < 72.25
