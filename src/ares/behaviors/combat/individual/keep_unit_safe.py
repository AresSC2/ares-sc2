from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
from sc2.position import Point2
from sc2.unit import Unit

from ares.behaviors.behavior import Behavior
from ares.behaviors.combat.individual.combat_individual_behavior import (
    CombatIndividualBehavior,
)
from ares.behaviors.combat.individual.path_unit_to_target import PathUnitToTarget
from ares.managers.manager_mediator import ManagerMediator

if TYPE_CHECKING:
    from ares import AresBot


@dataclass
class KeepUnitSafe(CombatIndividualBehavior):
    """Get a unit to safety based on the influence grid passed in.

    Example:
    ```py
    from ares.behaviors.combat import KeepUnitSafe

    unit: Unit
    grid: np.ndarray = self.mediator.get_ground_grid
    self.register_behavior(KeepUnitSafe(unit, grid))
    ```

    Attributes
    ----------
    unit : Unit
        The unit to stay safe.
    grid : np.ndarray
        2D Grid which usually contains enemy influence.
    """

    unit: Unit
    grid: np.ndarray

    def execute(self, ai: "AresBot", config: dict, mediator: ManagerMediator) -> bool:
        # no action executed
        if mediator.is_position_safe(grid=self.grid, position=self.unit.position):
            return False
        else:
            safe_spot: Point2 = mediator.find_closest_safe_spot(
                from_pos=self.unit.position, grid=self.grid
            )
            path: Behavior = PathUnitToTarget(
                unit=self.unit,
                grid=self.grid,
                target=safe_spot,
                success_at_distance=0.0,
            )
            return path.execute(ai, config, mediator)
