from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

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
class AMove(CombatIndividualBehavior):
    """A-Move a unit to a target.

    Example:
    ```py
    from ares.behaviors.combat.individual import AMove

    self.register_behavior(AMove(unit, self.game_info.map_center))
    ```

    Attributes:
        unit: The unit to stay safe.
        target: Where the unit is going.
        success_at_distance: Distance at which we don't need to issue
            a new move command because it's near the target.

    """

    unit: Unit
    target: Union[Point2, Unit]
    success_at_distance: float = 7.0

    def execute(self, ai: "AresBot", config: dict, mediator: ManagerMediator) -> bool:
        if (
            self.success_at_distance > 0
            and cy_distance_to(self.unit.position, self.target.position)
            < self.success_at_distance
        ):
            return False
        self.unit.attack(self.target)
        return True
