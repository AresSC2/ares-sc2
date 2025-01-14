from dataclasses import dataclass
from typing import TYPE_CHECKING

from cython_extensions import cy_closest_to
from sc2.ids.ability_id import AbilityId
from sc2.position import Point2
from sc2.unit import Unit

from ares.behaviors.combat.individual import CombatIndividualBehavior
from ares.consts import ALL_STRUCTURES
from ares.managers.manager_mediator import ManagerMediator

if TYPE_CHECKING:
    from ares import AresBot


@dataclass
class RavenAutoTurret(CombatIndividualBehavior):
    """Drop a turret, opinionated and could be improved
    Create own behavior based on this if needed.

    Attributes:
        unit: Unit
        all_close_enemy: All close by allied units we want to heal.
    """

    unit: Unit
    all_close_enemy: list[Unit]

    def execute(self, ai: "AresBot", config: dict, mediator: ManagerMediator) -> bool:
        if AbilityId.BUILDAUTOTURRET_AUTOTURRET not in self.unit.abilities:
            return False

        only_enemy_units: list[Unit] = [
            u for u in self.all_close_enemy if u.type_id not in ALL_STRUCTURES
        ]

        if len(only_enemy_units) <= 1:
            return False

        if (
            ai.get_total_supply(only_enemy_units) > 3
            and AbilityId.BUILDAUTOTURRET_AUTOTURRET in self.unit.abilities
        ):
            target: Point2 = cy_closest_to(
                self.unit.position, only_enemy_units
            ).position.towards(self.unit, 3.0)
            if not ai.in_placement_grid(target):
                return False

            self.unit(AbilityId.BUILDAUTOTURRET_AUTOTURRET, target)
            return True

        if self.all_close_enemy and not only_enemy_units:
            target: Point2 = cy_closest_to(
                self.unit.position, self.all_close_enemy
            ).position.towards(self.unit, 3.0)
            if not ai.in_placement_grid(target):
                return False

            self.unit(AbilityId.BUILDAUTOTURRET_AUTOTURRET, target)
            return True

        if self.unit.is_using_ability(AbilityId.BUILDAUTOTURRET_AUTOTURRET):
            return True

        return False
