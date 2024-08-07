from dataclasses import dataclass
from typing import TYPE_CHECKING

from sc2.unit import Unit

from ares.behaviors.combat.individual.combat_individual_behavior import (
    CombatIndividualBehavior,
)
from ares.managers.manager_mediator import ManagerMediator

if TYPE_CHECKING:
    from ares import AresBot


@dataclass
class AttackTarget(CombatIndividualBehavior):
    """Shoot a target.

    Example:
    ```py
    from ares.behaviors.combat.individual import AttackTarget

    unit: Unit
    target: Unit
    self.register_behavior(AttackTarget(unit, target))
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
    extra_range: float = 0.0

    def execute(
        self, ai: "AresBot", config: dict, mediator: ManagerMediator, **kwargs
    ) -> bool:
        self.unit.attack(self.target)
        return True
