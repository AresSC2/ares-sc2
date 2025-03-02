from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
from cython_extensions import cy_distance_to
from sc2.ids.ability_id import AbilityId
from sc2.position import Point2
from sc2.unit import Unit

from ares.behaviors.combat.individual.combat_individual_behavior import (
    CombatIndividualBehavior,
)
from ares.behaviors.combat.individual.path_unit_to_target import PathUnitToTarget
from ares.behaviors.combat.individual.use_ability import UseAbility
from ares.managers.manager_mediator import ManagerMediator

if TYPE_CHECKING:
    from ares import AresBot


@dataclass
class MoveToSafeTarget(CombatIndividualBehavior):
    """Given a destination `target`, find the nearest safe position and move
    unit there.

    Example:
    ```py
    from ares.behaviors.combat.individual import MoveToSafeTarget

    unit: Unit
    grid: np.ndarray = self.mediator.get_ground_grid
    target: Point2 = self.game_info.map_center
    self.register_behavior(MoveToSafeTarget(unit, grid, target))
    ```

    Attributes:
        unit: The unit to path.
        grid: 2D grid to path on.
        target: Target destination.
        use_pathing: Whether to use pathing or just move directly towards the target.
            Defaults to True.
        success_at_distance: If the unit has gotten this close, consider path
            behavior complete. Defaults to 0.0.
        sensitivity: Path precision. Defaults to 5.
        smoothing: Whether to smooth out the path. Defaults to False.
        sense_danger: Whether to check for dangers. If none are present,
            the pathing query is skipped. Defaults to True.
        danger_distance: If `sense_danger` is True, how far to check for dangers.
            Defaults to 20.0.
        danger_threshold: Influence at which a danger is respected.
            Defaults to 5.0.
        radius: How far to look for a safe spot around the target.
            Defaults to 12.0.

    """

    unit: Unit
    grid: np.ndarray
    target: Point2
    use_pathing: bool = True
    success_at_distance: float = 1.0
    sensitivity: int = 5
    smoothing: bool = False
    sense_danger: bool = True
    danger_distance: float = 20.0
    danger_threshold: float = 5.0
    radius: float = 12.0

    def execute(self, ai: "AresBot", config: dict, mediator: ManagerMediator) -> bool:
        if cy_distance_to(self.unit.position, self.target) <= self.success_at_distance:
            return False

        safe_spot: Point2 = mediator.find_closest_safe_spot(
            from_pos=self.target, grid=self.grid, radius=self.radius
        )
        if self.use_pathing:
            return PathUnitToTarget(
                unit=self.unit,
                grid=self.grid,
                target=safe_spot,
                success_at_distance=self.success_at_distance,
                sensitivity=self.sensitivity,
                sense_danger=self.sense_danger,
                smoothing=self.smoothing,
            ).execute(ai, config, mediator)
        else:
            return UseAbility(AbilityId.MOVE_MOVE, self.unit, safe_spot).execute(
                ai, config, mediator
            )
