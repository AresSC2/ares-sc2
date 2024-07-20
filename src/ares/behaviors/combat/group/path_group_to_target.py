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

    Attributes
    ----------
    start : Point2
        Where to start the path query.
    group: list[Unit]
        The actual group units.
    group_tags : set[int]
        The units to path.
    grid : np.ndarray
        2D Grid to path on.
    target : Point2
        Target destination.
    success_at_distance : float (default: 0.0)
        If unit has got this close, consider path behavior complete.
    sensitivity : int (default: 5)
        Path precision.
    smoothing : bool (default: False)
        Smooth out the path.
    sense_danger : bool (default: False)
        Check for dangers, if none are present pathing query is skipped.
    danger_distance : float (default: 20.0)
        If sense_danger=True, how far to check for dangers?
    danger_threshold : float (default: 5.0)
        Influence at which a danger is respected.
    prevent_duplicate : bool (default: True)
        Try to prevent spamming action.
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
