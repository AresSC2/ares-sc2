from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
from cython_extensions import cy_distance_to
from sc2.position import Point2
from sc2.unit import Unit

from ares.behaviors.combat.individual.combat_individual_behavior import (
    CombatIndividualBehavior,
)
from ares.managers.manager_mediator import ManagerMediator

if TYPE_CHECKING:
    from ares import AresBot


@dataclass
class PathUnitToTarget(CombatIndividualBehavior):
    """Path a unit to its target destination.

    TODO: Add attack enemy in range logic / parameter
        Not added yet since that may be it's own Behavior

    Example:
    ```py
    from ares.behaviors.combat import PathUnitToTarget

    unit: Unit
    grid: np.ndarray = self.mediator.get_ground_grid
    target: Point2 = self.game_info.map_center
    self.register_behavior(PathUnitToTarget(unit, grid, target))
    ```

    Attributes
    ----------
    unit : Unit
        The unit to path.
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
    sense_danger : bool (default: True)
        Check for dangers, if none are present pathing query is skipped.
    danger_distance : float (default: 20.0)
        If sense_danger=True, how far to check for dangers?
    danger_threshold : float (default: 5.0)
        Influence at which a danger is respected.
    """

    unit: Unit
    grid: np.ndarray
    target: Point2
    success_at_distance: float = 0.0
    sensitivity: int = 5
    smoothing: bool = False
    sense_danger: bool = True
    danger_distance: float = 20.0
    danger_threshold: float = 5.0

    def execute(self, ai: "AresBot", config: dict, mediator: ManagerMediator) -> bool:
        distance_to_target: float = cy_distance_to(self.unit.position, self.target)
        # no action executed
        if distance_to_target < self.success_at_distance:
            return False

        move_to: Point2 = mediator.find_path_next_point(
            start=self.unit.position,
            target=self.target,
            grid=self.grid,
            sensitivity=self.sensitivity,
            smoothing=self.smoothing,
            sense_danger=self.sense_danger,
            danger_distance=self.danger_distance,
            danger_threshold=self.danger_threshold,
        )
        self.unit.move(move_to)
        return True
