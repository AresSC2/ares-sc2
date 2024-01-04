from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

import numpy as np
from sc2.ids.ability_id import AbilityId
from sc2.position import Point2
from sc2.unit import Unit

from ares.behaviors.combat.group import CombatGroupBehavior
from ares.cython_extensions.units_utils import cy_sorted_by_distance_to
from ares.managers.manager_mediator import ManagerMediator

if TYPE_CHECKING:
    from ares import AresBot


@dataclass
class StutterGroupBack(CombatGroupBehavior):
    """Stutter a group back in unison.


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
    grid : np.ndarray
        Grid this group will use to path on.
    """

    group: list[Unit]
    group_tags: set[int]
    group_position: Point2
    target: Union[Point2, Unit]
    grid: np.ndarray

    def execute(self, ai: "AresBot", config: dict, mediator: ManagerMediator) -> bool:
        if len(self.group) == 0:
            return False

        sorted_units: list[Unit] = cy_sorted_by_distance_to(
            self.group, self.target, reverse=True
        )
        sample_unit: Unit = sorted_units[0]

        if self.group_weapons_on_cooldown(self.group, stutter_forward=False):
            if self.duplicate_or_similar_order(
                sample_unit, self.target, AbilityId.MOVE
            ):
                return True
            group_move_to: Point2 = mediator.find_path_next_point(
                start=self.group_position,
                target=ai.start_location,
                grid=self.grid,
                sensitivity=9,
            )
            if self.duplicate_or_similar_order(
                sample_unit, self.target, AbilityId.MOVE
            ):
                return True
            ai.give_same_action(AbilityId.MOVE, self.group_tags, group_move_to)
        else:
            if self.duplicate_or_similar_order(
                sample_unit, self.target, AbilityId.ATTACK
            ):
                return True
            ai.give_same_action(AbilityId.ATTACK, self.group_tags, self.target)

        return True
