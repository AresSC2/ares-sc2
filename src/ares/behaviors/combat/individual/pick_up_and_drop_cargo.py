from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, Union

import numpy as np
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units

from ares.behaviors.combat.individual import DropCargo, KeepUnitSafe, PathUnitToTarget
from ares.behaviors.combat.individual.combat_individual_behavior import (
    CombatIndividualBehavior,
)
from ares.behaviors.combat.individual.pick_up_cargo import PickUpCargo
from ares.consts import UnitRole
from ares.managers.manager_mediator import ManagerMediator

if TYPE_CHECKING:
    from ares import AresBot


@dataclass
class PickUpAndDropCargo(CombatIndividualBehavior):
    """Combines `PickUpCargo` and `DropCargo` behaviors.

    Medivacs, WarpPrism, Overlords.

    Example:
    ```py
    from ares.behaviors.combat.individual import PickUpAndDropCargo

    unit: Unit # medivac for example
    grid: np.ndarray = self.mediator.get_ground_grid
    pickup_targets: Union[Units, list[Unit]] = self.workers
    self.register_behavior(
        PickUpAndDropCargo(unit, grid, pickup_targets, self.ai.game_info.map_center)
    )
    ```

    Attributes:
        unit: The container unit.
        grid: Pathing grid for the container unit.
        pickup_targets: Units we want to load into the container.
        target: Drop at this target
        cargo_switch_to_role: Sometimes useful to switch cargo to
            a new role immediately after loading. Defaults to None.
        should_drop_units: Whether to drop units once they are loaded.
            Defaults to True.
        keep_dropship_safe: If true, will keep dropship safe if nothing else to do.
            Defaults to True.
        success_at_distance: Distance at which pathing to target stops being checked.
            Defaults to 2.0.

    """

    unit: Unit
    grid: np.ndarray
    pickup_targets: Union[Units, list[Unit]]
    target: Point2
    cargo_switch_to_role: Optional[UnitRole] = None
    should_drop_units: bool = True
    keep_dropship_safe: bool = True
    success_at_distance: float = 2.0

    def execute(self, ai: "AresBot", config: dict, mediator: ManagerMediator) -> bool:
        # check for units to pick up.
        if PickUpCargo(
            unit=self.unit,
            grid=self.grid,
            pickup_targets=self.pickup_targets,
            cargo_switch_to_role=self.cargo_switch_to_role,
        ).execute(ai, config, mediator):
            return True

        if self.unit.has_cargo:
            # path to target
            if PathUnitToTarget(
                unit=self.unit,
                grid=self.grid,
                target=self.target,
                success_at_distance=self.success_at_distance,
            ).execute(ai, config, mediator):
                return True
            if self.should_drop_units:
                if DropCargo(unit=self.unit, target=self.unit.position).execute(
                    ai, config, mediator
                ):
                    return True

            if self.keep_dropship_safe and KeepUnitSafe(
                unit=self.unit, grid=self.grid
            ).execute(ai, config, mediator):
                return True

        return False
