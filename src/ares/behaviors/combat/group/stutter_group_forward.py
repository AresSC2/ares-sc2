from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

from sc2.ids.ability_id import AbilityId
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units

from ares.behaviors.combat.group.combat_group_behavior import CombatGroupBehavior
from ares.managers.manager_mediator import ManagerMediator
from cython_extensions import cy_in_attack_range, cy_sorted_by_distance_to
from src.ares.consts import UnitTreeQueryType

if TYPE_CHECKING:
    from ares import AresBot


@dataclass
class StutterGroupForward(CombatGroupBehavior):
    """Stutter a group forward in unison.

    Attributes
    ----------
    group : Unit
        The group of units we want to control.
    group_tags: Point2
        The group unit tags.
    group_position : Point2
        The position where this group is situated.
    target : Union[Point2, Unit]
        Target for the group.
    """

    group: list[Unit]
    group_tags: set[int]
    group_position: Point2
    target: Union[Point2, Unit]

    def execute(self, ai: "AresBot", config: dict, mediator: ManagerMediator) -> bool:
        if len(self.group) == 0:
            return False

        sorted_units: list[Unit] = cy_sorted_by_distance_to(self.group, self.target)
        sample_unit: Unit = sorted_units[0]

        in_range: dict[int, Units] = mediator.get_units_in_range(
            start_points=self.group,
            distances=12.0,
            query_tree=UnitTreeQueryType.AllEnemy,
            return_as_dict=True,
        )

        # if all units are in range of something, don't worry about moving
        all_in_range: bool = True
        for unit in self.group:
            enemy: Units = in_range[unit.tag]
            in_attack_range: list[Unit] = cy_in_attack_range(unit, enemy)

            if not in_attack_range:
                all_in_range = False
                break

        # if the whole group are in range of something, then don't bother moving
        if all_in_range:
            if self.duplicate_or_similar_order(
                sample_unit, self.target, AbilityId.ATTACK
            ):
                ai.give_same_action(AbilityId.ATTACK, self.group_tags, self.target)
                return True

            return True

        if self.group_weapons_on_cooldown(self.group, stutter_forward=True):
            if self.duplicate_or_similar_order(
                sample_unit, self.target, AbilityId.MOVE
            ):
                return True
            ai.give_same_action(AbilityId.MOVE, self.group_tags, self.target)
        else:
            if self.duplicate_or_similar_order(
                sample_unit, self.target, AbilityId.ATTACK
            ):
                return True
            ai.give_same_action(AbilityId.ATTACK, self.group_tags, self.target)

        return True
