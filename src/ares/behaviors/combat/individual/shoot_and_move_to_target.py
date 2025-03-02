from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units

from ares.behaviors.combat.individual import PathUnitToTarget
from ares.behaviors.combat.individual.combat_individual_behavior import (
    CombatIndividualBehavior,
)
from ares.behaviors.combat.individual.shoot_target_in_range import ShootTargetInRange
from ares.managers.manager_mediator import ManagerMediator

if TYPE_CHECKING:
    from ares import AresBot


@dataclass
class ShootAndMoveToTarget(CombatIndividualBehavior):
    """We want to move to a specific point on the map, but shoot
        any in range enemies along the way.
        Can also optionally shoot destructables.
        If unit is left near target
        it gets a moved, so keep in mind when calling this method.

    Example:
    ```py
    from ares.behaviors.combat.individual import ShootAndMoveToTarget
    self.ai.register_behavior(ShootAndMoveToTarget(
        unit=unit,
        enemy_units=enemies,
        target=target,
        grid=grid,
    ))
    ```

    Attributes:
        unit: The unit we want tp control.
        enemy_units: The units that we will shoot at while moving.
        target: The position where we want our unit to end up.
        grid: Grid used for pathfinding.
        dist_to_target: Distance away from target where pathfinding stops.
            Default value of 4.0 means that once within 4 tiles of the target
            we stop pathfinding.
        attack_destructables: Whether we should shoot destructibles.
            Default value is `True`.
    """

    unit: Unit
    enemy_units: Units | list[Unit]
    target: Point2
    grid: np.ndarray
    dist_to_target: float = 4.0
    attack_destructables: bool = True

    def execute(self, ai: "AresBot", config: dict, mediator: ManagerMediator) -> bool:
        if ShootTargetInRange(self.unit, self.enemy_units).execute(
            ai, config, mediator
        ):
            return True

        if self.attack_destructables and ShootTargetInRange(
            self.unit, ai.destructables
        ).execute(ai, config, mediator):
            return True

        if PathUnitToTarget(
            unit=self.unit,
            grid=self.grid,
            target=self.target,
            success_at_distance=self.dist_to_target,
        ):
            return True

        return False
