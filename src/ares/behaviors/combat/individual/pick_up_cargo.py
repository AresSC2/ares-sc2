from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, Union

import numpy as np
from cython_extensions import cy_closest_to, cy_distance_to
from sc2.ids.ability_id import AbilityId
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units

from ares.behaviors.combat.individual.combat_individual_behavior import (
    CombatIndividualBehavior,
)
from ares.consts import UnitRole
from ares.dicts.pickup_range import PICKUP_RANGE
from ares.managers.manager_mediator import ManagerMediator

if TYPE_CHECKING:
    from ares import AresBot


@dataclass
class PickUpCargo(CombatIndividualBehavior):
    """Handle loading cargo into a container.

    Medivacs, WarpPrism, Overlords, Nydus.

    Example:
    ```py
    from ares.behaviors.combat import PickUpCargo

    unit: Unit # medivac for example
    grid: np.ndarray = self.mediator.get_ground_grid
    pickup_targets: Union[Units, list[Unit]] = self.workers
    self.register_behavior(PickUpCargo(unit, grid, pickup_targets))
    ```

    Attributes
    ----------
    unit : Unit
        The container unit.
    grid : np.ndarray
        Pathing grid for container unit.
    pickup_targets : Union[Units, list[Unit]]
        Units we want to load into the container.
    cargo_switch_to_role : UnitRole (default: None)
        Sometimes useful to switch cargo tp new role
        immediately after loading.
    """

    unit: Unit
    grid: np.ndarray
    pickup_targets: Union[Units, list[Unit]]
    cargo_switch_to_role: Optional[UnitRole] = None

    def execute(self, ai: "AresBot", config: dict, mediator: ManagerMediator) -> bool:
        # no action executed
        if not self.pickup_targets or self.unit.type_id not in PICKUP_RANGE:
            # just ensure tags inside are assigned correctly
            if len(self.unit.passengers_tags) > 0 and self.cargo_switch_to_role:
                for tag in self.unit.passengers_tags:
                    mediator.assign_role(tag=tag, role=self.cargo_switch_to_role)
            return False

        unit_pos: Point2 = self.unit.position
        target: Unit = cy_closest_to(unit_pos, self.pickup_targets)
        distance: float = cy_distance_to(self.unit.position, target.position)

        if distance <= PICKUP_RANGE[self.unit.type_id]:
            self.unit(AbilityId.SMART, target)
        else:
            move_to: Point2 = mediator.find_path_next_point(
                start=unit_pos, target=target.position, grid=self.grid
            )
            self.unit.move(move_to)

        return True
