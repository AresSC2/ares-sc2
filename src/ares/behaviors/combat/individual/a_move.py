from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

from sc2.position import Point2
from sc2.unit import Unit

from ares.behaviors.combat import CombatBehavior
from ares.managers.manager_mediator import ManagerMediator

if TYPE_CHECKING:
    from ares import AresBot


@dataclass
class AMove(CombatBehavior):
    """A-Move a unit to a target.

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
        return self.unit.attack(self.target)
