from dataclasses import dataclass

import numpy as np
from sc2.position import Point2
from sc2.unit import Unit

from ares.behaviors.combat import CombatManeuver
from ares.behaviors.combat.individual import PathUnitToTarget
from ares.managers.manager_mediator import ManagerMediator


@dataclass
class GeneralUnitRecipes:
    @staticmethod
    def move_to_safe_target(
        unit: Unit,
        grid: np.ndarray,
        target: Point2,
        mediator: ManagerMediator,
        success_at_distance: float = 0.0,
        radius: float = 12.0,
        sensitivity: int = 2,
        sense_danger: bool = True,
        smoothing: bool = False,
    ) -> CombatManeuver:
        """Given a target, find the closest safe tile nearby. Then path
        unit to the calculated safe target.

        Example:
        ```
        self.ai.register_behavior(
            GeneralUnitRecipes.move_to_safe_target(
                unit,
                self.mediator.get_ground_grid,
                self.game_info.map_center,
                self.mediator
            )
        )
        ```
        Parameters:
            unit: The unit to control.
            grid: The grid this unit should path on.
            target: The general target for the unit to move to.
            mediator: A reference to the ares-sc2 mediator object.
            success_at_distance: The distance from the target at which
                the pathing task is considered complete.
                Defaults to 0.0
            radius: The radius to search for safe spots.
                Defaults to 12.
            sensitivity: The precision of the pathing query.
                A value of 1 indicates highly accurate pathing.
                Defaults to 2.
            sense_danger: Whether to search for nearby danger on the grid.
                If no danger is found, the pathing query will be skipped.
                Defaults to True.
            smoothing: Whether to smooth out the path.
                Defaults to False.


        Returns: CombatManeuver
            A CombatManeuver object with a single PathUnitToTarget behavior.
        """
        maneuver: CombatManeuver = CombatManeuver()
        safe_spot: Point2 = mediator.find_closest_safe_spot(
            from_pos=target, grid=grid, radius=radius
        )
        maneuver.add(
            PathUnitToTarget(
                unit=unit,
                grid=grid,
                target=safe_spot,
                success_at_distance=success_at_distance,
                sensitivity=sensitivity,
                sense_danger=sense_danger,
                smoothing=smoothing,
            )
        )
        return maneuver
