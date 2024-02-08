from dataclasses import dataclass
from typing import TYPE_CHECKING

from cython_extensions import cy_attack_ready
from sc2.unit import Unit

from ares.behaviors.combat.individual import AttackTarget
from ares.behaviors.combat.individual.combat_individual_behavior import (
    CombatIndividualBehavior,
)
from ares.managers.manager_mediator import ManagerMediator

if TYPE_CHECKING:
    from ares import AresBot


@dataclass
class StutterUnitForward(CombatIndividualBehavior):
    """Shoot at the target if possible, else move back.

    Example:
    ```py
    from ares.behaviors.combat import StutterUnitForward

    unit: Unit
    target: Unit
    self.register_behavior(StutterUnitForward(unit, target))
    ```

    Attributes
    ----------
    unit: Unit
        The unit to shoot.
    target : Unit
        The unit we want to shoot at.
    """

    unit: Unit
    target: Unit

    def execute(
        self, ai: "AresBot", config: dict, mediator: ManagerMediator, **kwargs
    ) -> bool:
        unit = self.unit
        target = self.target
        if cy_attack_ready(ai, unit, target):
            return AttackTarget(unit=unit, target=target).execute(ai, config, mediator)
        else:
            unit.move(target.position)
            return True
