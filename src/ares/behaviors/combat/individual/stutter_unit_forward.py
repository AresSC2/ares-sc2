from dataclasses import dataclass
from typing import TYPE_CHECKING

from sc2.unit import Unit

from ares.behaviors.combat import CombatBehavior
from ares.behaviors.combat.individual import AttackTarget
from ares.cython_extensions.combat_utils import cy_attack_ready
from ares.managers.manager_mediator import ManagerMediator

if TYPE_CHECKING:
    from ares import AresBot


@dataclass
class StutterUnitForward(CombatBehavior):
    """Shoot at the target if possible, else move back.

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
        """Shoot at the target if possible, else kite back.

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
        unit = self.unit
        target = self.target
        if not target.is_memory and cy_attack_ready(ai, unit, target):
            return AttackTarget(unit=unit, target=target).execute(ai, config, mediator)
        else:
            unit.move(target.position)
            return True
