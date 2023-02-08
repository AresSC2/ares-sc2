"""Base class for Managers.

"""
from abc import ABCMeta, abstractmethod
from typing import Any, Dict

from consts import ManagerName, ManagerRequestType
from custom_bot_ai import CustomBotAI
from managers.manager_mediator import ManagerMediator
from sc2.units import Units


class Manager(metaclass=ABCMeta):
    """Base class for Managers.

    Attributes
    ----------
    ai :
        Bot object that will be running the game
    config :
        Dictionary with the data from the configuration file
    mediator :
        ManagerMediator used for getting information from other managers.
    empty_units :
        Empty Units object that's often useful to have around.

    """

    def __init__(
        self, ai: CustomBotAI, config: Dict, mediator: ManagerMediator
    ) -> None:
        """Set up the manager.

        Parameters
        ----------
        ai :
            Bot object that will be running the game
        config :
            Dictionary with the data from the configuration file
        mediator :
            ManagerMediator used for getting information from other managers.

        Returns
        -------

        """
        super().__init__()
        self.ai: CustomBotAI = ai
        self.config: Dict = config
        self.manager_mediator: ManagerMediator = mediator
        self.empty_units: Units = Units([], self.ai)

    async def initialise(self) -> None:
        """Supply the manager with information that requires the game to have launched.

        Returns
        -------

        """
        pass

    def manager_request(
        self,
        receiver: ManagerName,
        request: ManagerRequestType,
        reason: str = None,
        **kwargs
    ) -> Any:
        """To be implemented by managers that inherit from IManagerMediator interface.

        Parameters
        ----------
        receiver :
            The Manager the request is being sent to.
        request :
            The Manager that made the request
        reason :
            Why the Manager has made the request
        kwargs :
            If the ManagerRequest is calling a function, that function's keyword
            arguments go here.

        Returns
        -------

        """
        pass

    @abstractmethod
    async def update(self, iteration: int) -> None:
        """Update the Manager.

        Parameters
        ----------
        iteration :
            The game iteration.

        Returns
        -------

        """
        pass
