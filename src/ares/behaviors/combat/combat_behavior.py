from typing import TYPE_CHECKING, Protocol

from ares.behaviors.behavior import Behavior
from ares.managers.manager_mediator import ManagerMediator

if TYPE_CHECKING:
    from ares import AresBot


class CombatBehavior(Behavior, Protocol):
    """Interface that all combat behaviors should adhere to."""

    def execute(self, ai: "AresBot", config: dict, mediator: ManagerMediator) -> bool:
        """Execute the implemented behavior.

        Compared to CombatBehavior a MacroBehavior may be a larger isolated task.
        No need to return anything for a macro behavior.

        Parameters
        ----------
        ai :
            Bot object that will be running the game.
        config :
            Dictionary with the data from the configuration file.
        mediator :
            ManagerMediator used for getting information from other managers.

        Returns
        ----------
        bool :
            MacroBehavior carried out an action.
        """
        ...
