from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

import numpy as np
from cython_extensions import cy_attack_ready
from loguru import logger
from sc2.unit import Unit

from ares.behaviors.combat.individual import AttackTarget, KeepUnitSafe
from ares.behaviors.combat.individual.combat_individual_behavior import (
    CombatIndividualBehavior,
)
from ares.managers.manager_mediator import ManagerMediator

if TYPE_CHECKING:
    from ares import AresBot


@dataclass
class StutterUnitBack(CombatIndividualBehavior):
    """Shoot at the target if possible, else move back.

    Example:
    ```py
    from ares.behaviors.combat import StutterUnitBack

    unit: Unit
    target: Unit
    self.register_behavior(StutterUnitBack(unit, target))
    ```

    Attributes
    ----------
    unit: Unit
        The unit to shoot.
    target : Unit
        The unit we want to shoot at.
    kite_via_pathing : bool
        Kite back using pathing? Value for `grid` must be present.
    grid : Optional[np.ndarray]
        Pass in if using kite_via_pathing.
    """

    unit: Unit
    target: Unit
    kite_via_pathing: bool = True
    grid: Optional[np.ndarray] = None

    def execute(
        self, ai: "AresBot", config: dict, mediator: ManagerMediator, **kwargs
    ) -> bool:
        unit = self.unit
        target = self.target
        if self.kite_via_pathing and self.grid is None:
            self.grid = mediator.get_ground_grid

        if cy_attack_ready(ai, unit, target):
            return AttackTarget(unit=unit, target=target).execute(ai, config, mediator)
        elif self.kite_via_pathing and self.grid is not None:
            return KeepUnitSafe(unit=unit, grid=self.grid).execute(ai, config, mediator)
        # TODO: Implement non pathing kite back
        else:
            logger.warning("Stutter back doesn't work for kite_via_pathing=False yet")
            return False
