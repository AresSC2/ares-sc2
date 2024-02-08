from dataclasses import dataclass

import numpy as np
from cython_extensions import cy_distance_to
from sc2.position import Point2
from sc2.unit import Unit

from ares.behaviors.combat import CombatManeuver
from ares.behaviors.combat.individual import (
    AMove,
    KeepUnitSafe,
    PathUnitToTarget,
    ShootTargetInRange,
)


@dataclass
class RangedMicroRecipes:
    @staticmethod
    def shoot_and_move_to_target(
        unit: Unit,
        enemy_units: list[Unit],
        target: Point2,
        grid: np.ndarray,
        dist_to_target: float = 4.0,
        keep_safe: bool = True,
    ) -> CombatManeuver:
        """We want to move to a specific point on the map, but shoot
        any in range enemies along the way. If unit is left near target
        it gets a moved, so keep in mind when calling this method.

        Example:
        ```
        self.ai.register_behavior(
            RangedMicroRecipes.shoot_and_move_to_target(
                unit,
                enemy_units,
                self.ai.game_info.map_center,
                self.mediator.get_ground_grid
            )
        )
        ```

        Parameters
        ----------
        unit :
            The unit we want to control
        enemy_units :
            The intended grid this unit should path on.
        target :
            General target this unit should move to.
        grid :
            Reference to ares-sc2 mediator object.
        dist_to_target :
            How far to search for safe spots.
        keep_safe :
            Should keep unit safe if nothing else to do?

        Returns
        -------
        CombatManeuver :
            A CombatManeuver object that should be registered.
        """
        ranged_micro_maneuver: CombatManeuver = CombatManeuver()
        ranged_micro_maneuver.add(ShootTargetInRange(unit, enemy_units))

        if cy_distance_to(unit.position, target) > dist_to_target:
            ranged_micro_maneuver.add(
                PathUnitToTarget(unit=unit, grid=grid, target=target)
            )
        else:
            ranged_micro_maneuver.add(AMove(unit, target))

        if keep_safe:
            ranged_micro_maneuver.add(KeepUnitSafe(unit, grid))

        return ranged_micro_maneuver

    @staticmethod
    def stutter_close_enemies_and_move_to_target(
        unit: Unit,
        enemy_units: list[Unit],
        target: Point2,
        grid: np.ndarray,
        dist_to_target: float = 2.5,
    ) -> CombatManeuver:
        """We want to move to a specific point on the map, but will
        happily take any fights along the way using stutter back
        micro. If unit is left near target
        it gets a moved, so keep in mind when calling this method.

        Example:
        ```
        self.ai.register_behavior(
            RangedMicroRecipes.stutter_back_and_path_to_target(
                unit,
                enemy_units,
                self.ai.game_info.map_center,
                self.mediator.get_ground_grid
            )
        )
        ```

        Parameters
        ----------
        unit :
            The unit we want to control
        enemy_units :
            The intended grid this unit should path on.
        target :
            General target this unit should move to.
        grid :
            Reference to ares-sc2 mediator object.
        dist_to_target :
            How far to search for safe spots.

        Returns
        -------
        CombatManeuver :
            A CombatManeuver object that should be registered.
        """
        ranged_micro_maneuver: CombatManeuver = CombatManeuver()

        if enemy_units:
            ranged_micro_maneuver.add(ShootTargetInRange(unit, enemy_units))

            ranged_micro_maneuver.add(KeepUnitSafe(unit, grid))

        else:
            if cy_distance_to(unit.position, target) > dist_to_target:
                ranged_micro_maneuver.add(
                    PathUnitToTarget(
                        unit=unit,
                        grid=grid,
                        target=target,
                        success_at_distance=1.0,
                    )
                )
            else:
                ranged_micro_maneuver.add(AMove(unit, target))

        return ranged_micro_maneuver
