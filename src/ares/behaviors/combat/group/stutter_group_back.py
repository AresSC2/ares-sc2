from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

import numpy as np
from cython_extensions import cy_distance_to_squared, cy_sorted_by_distance_to
from sc2.ids.ability_id import AbilityId
from sc2.position import Point2
from sc2.unit import Unit

from ares.behaviors.combat.group.combat_group_behavior import CombatGroupBehavior
from ares.managers.manager_mediator import ManagerMediator

if TYPE_CHECKING:
    from ares import AresBot

DIRECTIONS: list[Point2] = [
    Point2((1, 0)),
    Point2((-1, 0)),
    Point2((0, 1)),
    Point2((0, -1)),  # Cardinal directions
    Point2((1, 1)),
    Point2((-1, -1)),
    Point2((1, -1)),
    Point2((-1, 1)),  # Diagonal directions
]


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
            self.group, self.target.position, reverse=True
        )
        sample_unit: Unit = sorted_units[0]

        if self.group_weapons_on_cooldown(self.group, stutter_forward=False):
            group_safe: bool = True
            for unit in self.group:
                if not mediator.is_position_safe(
                    grid=self.grid, position=unit.position
                ):
                    group_safe = False
                    break
            if group_safe:
                return True
            if len(self.group) > 1:
                move_to_target: Point2 = self.calculate_retreat_position(ai)
                safe_spot: Point2 = mediator.find_closest_safe_spot(
                    from_pos=move_to_target, grid=self.grid
                )
            else:
                safe_spot: Point2 = mediator.find_closest_safe_spot(
                    from_pos=self.group_position, grid=self.grid
                )

            if ai.in_pathing_grid(safe_spot):
                group_move_to: Point2 = mediator.find_path_next_point(
                    start=self.group_position,
                    target=safe_spot,
                    grid=self.grid,
                    sensitivity=min(len(self.group), 8),
                )
                if self.duplicate_or_similar_order(
                    sample_unit, group_move_to, AbilityId.MOVE
                ):
                    return True
                ai.give_same_action(AbilityId.MOVE, self.group_tags, group_move_to)
        else:
            if self.duplicate_or_similar_order(
                sample_unit, self.target, AbilityId.ATTACK
            ):
                return True
            ai.give_same_action(AbilityId.ATTACK, self.group_tags, self.target.position)

        return True

    def calculate_retreat_position(self, ai: "AresBot") -> Point2:
        """
        Search 8 directions for somewhere to retreat to.

        Parameters
        ----------
        ai

        Returns
        -------

        """
        distance = len(self.group) * 1.5

        map_bounds = ai.game_info.map_size
        best_position: Point2 = self.group_position
        max_distance_from_target: float = 0.0

        for direction in DIRECTIONS:
            retreat_position: Point2 = self.group_position + direction * distance
            retreat_position = Point2(
                (
                    max(0, min(map_bounds[0] - 1, retreat_position.x)),
                    max(0, min(map_bounds[1] - 1, retreat_position.y)),
                )
            )

            if ai.in_pathing_grid(retreat_position):
                distance_from_target: float = cy_distance_to_squared(
                    self.target.position, retreat_position
                )

                if distance_from_target > max_distance_from_target:
                    max_distance_from_target = distance_from_target
                    best_position = retreat_position

        return best_position
