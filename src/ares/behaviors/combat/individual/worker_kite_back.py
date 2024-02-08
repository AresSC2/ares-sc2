from dataclasses import dataclass
from typing import TYPE_CHECKING

from cython_extensions import cy_attack_ready, cy_closest_to
from sc2.unit import Unit

from ares.behaviors.combat.individual import AttackTarget
from ares.behaviors.combat.individual.combat_individual_behavior import (
    CombatIndividualBehavior,
)
from ares.managers.manager_mediator import ManagerMediator

if TYPE_CHECKING:
    from ares import AresBot


@dataclass
class WorkerKiteBack(CombatIndividualBehavior):
    """Shoot at the target if possible, else move back.

    This is similar to stutter unit back, but takes advantage of
    mineral walking.

    Example:
    ```py
    from ares.behaviors.combat import WorkerKiteBack

    unit: Unit
    target: Unit
    self.register_behavior(
        WorkerKiteBack(
            unit, target
        )
    )
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
        if not target.is_memory and cy_attack_ready(ai, unit, target):
            return AttackTarget(unit=unit, target=target).execute(ai, config, mediator)
        elif mfs := ai.mineral_field:
            unit.gather(cy_closest_to(position=ai.start_location, units=mfs))
