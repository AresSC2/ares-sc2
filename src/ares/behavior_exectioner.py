from typing import TYPE_CHECKING

from ares.behaviors.behavior import Behavior
from ares.managers.manager_mediator import ManagerMediator

if TYPE_CHECKING:
    from ares import AresBot


class BehaviorExecutioner:
    """Executes behaviors added by the user each step.

    Users add behaviors from their own bot, this class will
    execute these tasks after the managers have updated.
    And clear out the `behaviors` list once complete.

    Attributes
    ----------
    ai : AresBot
        Bot object that will be running the game.
    config : dict
        Dictionary with the data from the configuration file.
    mediator : ManagerMediator
        Used for getting information from other managers.

    """

    def __init__(self, ai: "AresBot", config: dict, mediator: ManagerMediator):
        """Inits BehaviorExecutioner class."""
        self.ai: "AresBot" = ai
        self.config: dict = config
        self.mediator: ManagerMediator = mediator
        self.behaviors: list = []

    def register_behavior(self, behavior: Behavior) -> None:
        """Register behavior.

        Parameters
        ----------
        behavior : Behavior
            Class that follows the Behavior interface.

        Returns
        -------

        """
        self.behaviors.append(behavior)

    def execute(self) -> None:
        """Execute the list of behaviors, then empty the list.

        Returns
        -------

        """
        for behavior in self.behaviors:
            behavior.execute(self.ai, self.config, self.mediator)

        self.behaviors = []
