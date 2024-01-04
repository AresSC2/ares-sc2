from dataclasses import dataclass
from typing import TYPE_CHECKING

from sc2.position import Point2
from sc2.unit import Unit

from ares.behaviors.combat.individual.combat_individual_behavior import (
    CombatIndividualBehavior,
)
from ares.managers.manager_mediator import ManagerMediator

if TYPE_CHECKING:
    from ares import AresBot


@dataclass
class DropCargo(CombatIndividualBehavior):
    """Handle releasing cargo from a container.

    Medivacs, WarpPrism, Overlords, Nydus.

    Example:
    ```py
    from ares.behaviors.combat import DropCargo

    unit: Unit
    target: Unit
    self.register_behavior(DropCargo(unit, target))
    ```

    Attributes
    ----------
    unit : Unit
        The container unit.
    target : Point2
        The target position where to drop the cargo.
    """

    unit: Unit
    target: Point2

    def execute(self, ai: "AresBot", config: dict, mediator: ManagerMediator) -> bool:
        # TODO: Expand logic as needed, initial working version.
        # no action executed
        if self.unit.cargo_used == 0 or not ai.in_pathing_grid(self.unit.position):
            return False

        ai.do_unload_container(self.unit.tag)
        return True
