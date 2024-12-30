from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
from cython_extensions import cy_closest_to, cy_distance_to
from sc2.ids.ability_id import AbilityId
from sc2.position import Point2
from sc2.unit import Unit

from ares.behaviors.combat.group.combat_group_behavior import CombatGroupBehavior
from ares.managers.manager_mediator import ManagerMediator

if TYPE_CHECKING:
    from ares import AresBot


@dataclass
class PathGroupToTarget(CombatGroupBehavior):
    """Path a group to its target destination.

    We issue only one action for the whole group and
    attempt to filter spammed actions.


    Example:
    ```py
    from ares.behaviors.combat.group import PathGroupToTarget

    group: list[Unit] = [u for u in self.units]
    group_tags: set[int] = {u.tag for u in group}
    grid: np.ndarray = self.mediator.get_ground_grid
    start: Point2 = self.ai.start_location
    target: Point2 = self.game_info.map_center

    self.register_behavior(
        PathGroupToTarget(start, group, group_tags, grid, target)
    )
    ```

    Attributes:
        start: Where to start the path query.
        group: The actual group units.
        group_tags: The units to path.
        grid: 2D grid to path on.
        target: Target destination.
        success_at_distance: If the unit has gotten this close,
            consider the path behavior complete. Defaults to 0.0.
        sensitivity: Path precision. Defaults to 5.
        smoothing: Whether to smooth out the path. Defaults to False.
        sense_danger: Whether to check for dangers. If none are present,
            the pathing query is skipped. Defaults to False.
        danger_distance: If `sense_danger` is True, how far to check for dangers.
            Defaults to 20.0.
        danger_threshold: Influence at which a danger is respected.
            Defaults to 5.0.
        prevent_duplicate: Whether to try to prevent spamming actions.
            Defaults to True.
    """

    start: Point2
    group: list[Unit]
    group_tags: set[int]
    grid: np.ndarray
    target: Point2
    distance_check_squared: float = 26.25
    success_at_distance: float = 0.0
    sensitivity: int = 12
    smoothing: bool = False
    sense_danger: bool = False
    danger_distance: float = 20.0
    danger_threshold: float = 5.0
    prevent_duplicate: bool = True

    def execute(self, ai: "AresBot", config: dict, mediator: ManagerMediator) -> bool:
        assert isinstance(
            self.start, Point2
        ), f"{self.start} should be `Point2`, got {type(self.start)}"
        assert isinstance(
            self.target, Point2
        ), f"{self.target} should be `Point2`, got {type(self.target)}"

        if len(self.group) == 0:
            return False

        distance_to_target: float = cy_distance_to(self.start, self.target)
        # no action executed
        if distance_to_target < self.success_at_distance:
            return False

        move_to: Point2 = mediator.find_path_next_point(
            start=self.start,
            target=self.target,
            grid=self.grid,
            sensitivity=self.sensitivity,
            smoothing=self.smoothing,
            sense_danger=self.sense_danger,
            danger_distance=self.danger_distance,
            danger_threshold=self.danger_threshold,
        )

        if self.prevent_duplicate:
            sample_unit: Unit = cy_closest_to(self.start, self.group)

            if sample_unit and self.duplicate_or_similar_order(
                sample_unit,
                move_to,
                AbilityId.MOVE,
                distance_check_squared=self.distance_check_squared,
            ):
                return False

        ai.give_same_action(AbilityId.MOVE, self.group_tags, move_to)
        return True
