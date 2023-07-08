from dataclasses import dataclass
from typing import TYPE_CHECKING

from sc2.unit import Unit

from ares.behaviors.combat import CombatBehavior
from ares.behaviors.combat.individual import AttackTarget
from ares.cython_extensions.combat_utils import cy_attack_ready
from ares.cython_extensions.units_utils import cy_closest_to
from ares.managers.manager_mediator import ManagerMediator

if TYPE_CHECKING:
    from ares import AresBot


@dataclass
class WorkerKiteBack(CombatBehavior):
    """Shoot at the target if possible, else move back.

    This is similar to stutter unit back, but takes advantage of
    mineral walking.

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
        """Attack the target if possible, else mineral walk back.

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
        elif mfs := ai.mineral_field:
            unit.gather(cy_closest_to(position=ai.start_location, units=mfs))
