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
class NydusPathUnitToTarget(CombatIndividualBehavior):
    """Path a unit to its target destination, using nyduses if
    available.

    Example:
    ```py
    from ares.behaviors.combat.individual import NydusPathToTarget

    unit: Unit
    grid: np.ndarray = self.mediator.get_ground_grid
    target: Point2 = self.game_info.map_center
    self.register_behavior(NydusPathToTarget(unit, grid, target))
    ```

    Attributes:
        unit: The unit to path.
        grid: 2D grid to path on.
        target: Target destination.
        success_at_distance: float = 0.0
        large: Path large units. Defaults to False.
        sensitivity: Path precision. Defaults to 5.
        smoothing: Whether to smooth out the path. Defaults to False.
        exit_nydus_max_influence: Maximum enemy influence of nydus exit
            If above this value unit will not path through nydus. Defaults to 10.0.
    """

    unit: Unit
    grid: np.ndarray
    target: Point2
    success_at_distance: float = 0.0
    large: bool = (False,)
    sensitivity: int = 5
    smoothing: bool = False
    exit_nydus_max_influence: float = 10.0

    def execute(self, ai: "AresBot", config: dict, mediator: ManagerMediator) -> bool:
        distance_to_target: float = cy_distance_to(self.unit.position, self.target)
        # no action executed
        if distance_to_target < self.success_at_distance:
            return False

        point, exit_towards, nydus_tags = mediator.find_nydus_path_next_point(
            start=self.unit.position,
            target=self.target,
            grid=self.grid,
            sensitivity=self.sensitivity,
            smoothing=self.smoothing,
        )
        if (
            nydus_tags
            and mediator.is_position_safe(
                grid=self.grid,
                position=exit_towards,
                weight_safety_limit=self.exit_nydus_max_influence,
            )
            and self.unit.tag not in mediator.get_banned_nydus_travellers
        ):
            mediator.add_to_nydus_travellers(
                unit=self.unit,
                entry_nydus_tag=nydus_tags[0],
                exit_nydus_tag=nydus_tags[1],
                exit_towards=exit_towards,
            )

            if Point2(point) == ai.unit_tag_dict[nydus_tags[0]].position.rounded:
                self.unit.smart(ai.unit_tag_dict[nydus_tags[0]])
            else:
                self.unit.move(point)
        # No nydus tags, revert to normal pathing
        else:
            if point:
                self.unit.move(point)
            else:
                self.unit.move(self.target)

        return True
