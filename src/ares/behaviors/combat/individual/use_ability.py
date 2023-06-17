from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

from sc2.ids.ability_id import AbilityId
from sc2.position import Point2
from sc2.unit import Unit

from ares.behaviors.combat import CombatBehavior
from ares.managers.manager_mediator import ManagerMediator

if TYPE_CHECKING:
    from ares import AresBot


@dataclass
class UseAbility(CombatBehavior):
    """A-Move a unit to a target.

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
        """Use an ability with optional target.

        WARNING: This always returns True, so combat logic should
        reflect this.

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
        if self.target:
            self.unit(self.ability, self.target)
        else:
            self.unit(self.ability)

        return True
