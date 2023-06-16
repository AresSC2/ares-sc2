from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

import numpy as np
from loguru import logger
from sc2.unit import Unit

from ares.behaviors.combat import CombatBehavior
from ares.behaviors.combat.individual import AttackTarget, KeepUnitSafe
from ares.cython_extensions.combat_utils import cy_attack_ready
from ares.managers.manager_mediator import ManagerMediator

if TYPE_CHECKING:
    from ares import AresBot


@dataclass
class StutterUnitBack(CombatBehavior):
    """Shoot at the target if possible, else move back.

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
    kite_via_pathing: bool = False
    grid: Optional[np.ndarray] = None

    def execute(
        self, ai: "AresBot", config: dict, mediator: ManagerMediator, **kwargs
    ) -> bool:
        """Shoot at the target if possible, else kite back.

        Parameters
        ----------
        ai : AresBot
            Bot object that will be running the game
        config :
            Dictionary with the data from the configuration file
        mediator :
            ManagerMediator used for getting information from other managers.
        **kwargs :
            None

        Returns
        -------
        bool :
            CombatBehavior carried out an action.
        """
        unit = self.unit
        target = self.target
        if not target.is_memory and cy_attack_ready(ai, unit, target):
            return AttackTarget(unit=unit, target=target).execute(ai, config, mediator)
        elif self.kite_via_pathing and self.grid is not None:
            return KeepUnitSafe(unit=unit, grid=self.grid).execute(ai, config, mediator)
        # TODO: Implement non pathing kite back
        else:
            logger.warning("Stutter back doesn't work for kite_via_pathing=False yet")
            return False
