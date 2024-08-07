from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

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

    Attributes
    ----------
    unit : Unit
        The unit to stay safe.
    target: Point2
        Where the unit is going.
    """

    unit: Unit
    target: Union[Point2, Unit]

    def execute(self, ai: "AresBot", config: dict, mediator: ManagerMediator) -> bool:
        self.unit.attack(self.target)
        return True
