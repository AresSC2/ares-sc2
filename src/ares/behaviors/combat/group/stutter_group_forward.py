from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

from cython_extensions import cy_center, cy_in_attack_range, cy_sorted_by_distance_to
from sc2.ids.ability_id import AbilityId
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units

from ares.behaviors.combat.group.combat_group_behavior import CombatGroupBehavior
from ares.managers.manager_mediator import ManagerMediator

if TYPE_CHECKING:
    from ares import AresBot


@dataclass
class StutterGroupForward(CombatGroupBehavior):
    """Stutter a group forward in unison.

    Attributes
    ----------
    group : list[Unit]
        The group of units we want to control.
    group_tags: set[int]
        The group unit tags.
    group_position : Point2
        The position where this group is situated.
    target : Union[Point2, Unit]
        Target for the group.
        Used if no enemies present.
    enemies : Union[Units, list[Unit]]
        The enemy units we want to stutter towards
    """

    group: list[Unit]
    group_tags: set[int]
    group_position: Point2
    target: Union[Point2, Unit]
    enemies: Union[Units, list[Unit]]

    def execute(self, ai: "AresBot", config: dict, mediator: ManagerMediator) -> bool:
        if len(self.group) == 0:
            return False

        # no enemies, no actions to carry out
        if not self.enemies:
            return False

        sorted_units: list[Unit] = cy_sorted_by_distance_to(
            self.group, self.target.position
        )
        sample_unit: Unit = sorted_units[0]

        # if all units are in range of something, don't worry about moving
        all_in_range: bool = True
        enemy_center: Point2 = Point2(cy_center(self.enemies))
        for unit in self.group:
            in_attack_range: list[Unit] = cy_in_attack_range(unit, self.enemies)

            if not in_attack_range:
                all_in_range = False
                break

        # if the whole group are in range of something, then don't bother moving
        if all_in_range:
            if not self.duplicate_or_similar_order(
                sample_unit, self.target, AbilityId.ATTACK
            ):
                ai.give_same_action(AbilityId.ATTACK, self.group_tags, enemy_center)

            return True

        if self.group_weapons_on_cooldown(self.group, stutter_forward=True):
            if self.duplicate_or_similar_order(
                sample_unit, enemy_center, AbilityId.MOVE
            ):
                return True
            ai.give_same_action(AbilityId.MOVE, self.group_tags, enemy_center)
        else:
            if self.duplicate_or_similar_order(
                sample_unit, enemy_center, AbilityId.ATTACK
            ):
                return True
            ai.give_same_action(AbilityId.ATTACK, self.group_tags, enemy_center)

        return True
