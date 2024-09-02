from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

from sc2.ids.ability_id import AbilityId
from sc2.position import Point2
from sc2.unit import Unit

from ares.behaviors.combat.individual.combat_individual_behavior import (
    CombatIndividualBehavior,
)
from ares.managers.manager_mediator import ManagerMediator

if TYPE_CHECKING:
    from ares import AresBot


@dataclass
class UseAbility(CombatIndividualBehavior):
    """A-Move a unit to a target.

    Example:
    ```py
    from ares.behaviors.combat import UseAbility
    from sc2.ids.ability_id import AbilityId

    unit: Unit
    target: Union[Unit, Point2]
    self.register_behavior(
        UseAbility(
            AbilityId.FUNGALGROWTH_FUNGALGROWTH, unit, target
        )
    )
    ```

    Attributes
    ----------
    ability : AbilityId
        The ability we want to use.
    unit : Unit
        The unit to use the ability.
    target: Union[Point2, Unit, None]
        Target for this ability.
    """

    ability: AbilityId
    unit: Unit
    target: Union[Point2, Unit, None]

    def execute(
        self, ai: "AresBot", config: dict, mediator: ManagerMediator, **kwargs
    ) -> bool:
        if self.ability not in self.unit.abilities:
            return False

        if self.target:
            self.unit(self.ability, self.target)
        else:
            self.unit(self.ability)

        return True
