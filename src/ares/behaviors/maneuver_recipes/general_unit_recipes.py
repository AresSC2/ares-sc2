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

        Parameters
        ----------
        unit :
            The unit we want to control
        grid :
            The intended grid this unit should path on.
        target :
            General target this unit should move to.
        mediator :
            Reference to ares-sc2 mediator object.
        success_at_distance :
            If unit is within this distance to target,
            we consider the pathing task complete.
        radius :
            How far to search for safe spots.
        sensitivity :
            How precise the pathing query should be.
            1 for a highly accurate path
        sense_danger :
            Search for near danger on `grid`
            If none are found, skip pathing query
        smoothing :
            Smooth out the path

        Returns
        -------
        CombatManeuver :
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
