from dataclasses import dataclass
from typing import TYPE_CHECKING

from sc2.unit import Unit

from ares.behaviors.combat import CombatBehavior
from ares.managers.manager_mediator import ManagerMediator

if TYPE_CHECKING:
    from ares import AresBot


@dataclass
class AttackTarget(CombatBehavior):
    """Find something to shoot at.

    TODO: Currently only picks lowest health.
        Might want to pick best one shot KO for example

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
        """Attack something.

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

        self.unit.attack(self.target)
        return True
