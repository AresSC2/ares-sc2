"""Runner for build orders.

The main objective of this file is to read build orders from
the config file. Each item in the build order is a BuildOrderStep
object, with many instances of these making up a BuildOrder

"""

from typing import Callable, Dict, List, Optional, Set, Union

from loguru import logger
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId as UnitID
from sc2.ids.upgrade_id import UpgradeId
from sc2.position import Point2

from ares.consts import (
    BUILDS,
    DEBUG,
    OPENING_BUILD_ORDER,
    ManagerName,
    ManagerRequestType,
)
from ares.custom_bot_ai import CustomBotAI
from ares.managers.manager_mediator import ManagerMediator


class BuildOrderStep:
    """Individual BuildOrderStep.

    Attributes
    ----------
    command : Union[AbilityId, UnitID, UpgradeId]
        What should happen in this step of the build order.

        Examples
        --------
        Extractor trick : AbilityId.CANCEL
        Train a Drone : UnitID.DRONE
        Research Zergling Speed: UpgradeId.ZERGLINGMOVEMENTSPEED

    command_started: bool
        Whether this step has started
    start_condition: Callable
        What should be checked to determine when this step should start
    end_condition: Callable
        What should be checked to determine when this step has been completed
    target: str
        Specifier in the case that additional information is needed to complete the step

    """

    def __init__(
        self,
        command: Union[AbilityId, UnitID, UpgradeId],
        start_condition: Callable,
        end_condition: Callable,
        target: str = "",
    ) -> None:
        self.command: Union[AbilityId, UnitID, UpgradeId] = command
        self.command_started: bool = False
        self.start_condition: Callable = start_condition
        self.end_condition: Callable = end_condition
        self.target: str = target


class BuildRunner:
    """Parse and run a build order.

    Attributes
    ----------
    LOGGING_COMMANDS :
        Commands that should be written to the logs when started
    STRUCTURE_COMMANDS :
        Commands that are used to build structures. Specified for logging purposes
        regarding supply.
    build_order :
        List of BuildOrderSteps representing the build order.

    ai :
        CustomBotAI object that will be running the build.
    build_step :
        Current index of build order.
    config :
        Dictionary containing configuration details, i.e. the build order as a string.
    current_step_started :
        Whether the current step has been started.
    debug :
        Whether the bot is being run in debug mode.
        Note: this is separate from IDE debug settings.
    manager_mediator :
        ManagerMediator object used for getting information from other managers.
    opening_build_complete :
        Whether the specified build order has been completed.

    """

    LOGGING_COMMANDS: Set[UnitID] = {}
    STRUCTURE_COMMANDS: Set[UnitID] = {}

    build_order: List[BuildOrderStep]

    def __init__(
        self,
        ai: CustomBotAI,
        config: Dict,
        manager_mediator: ManagerMediator,
    ) -> None:
        """Set the runner to the beginning of the build order.

        Parameters
        ----------
        ai :
            CustomBotAI object that will be running the build.
        config :
            Dictionary containing configuration details, i.e. the build order as a
            string.
        manager_mediator :
            ManagerMediator object used for getting information from other managers.
        """
        self.ai: CustomBotAI = ai
        self.config: Dict = config
        self.build_step: int = 0
        self.debug: bool = config[DEBUG]
        self.current_step_started: bool = False
        self.manager_mediator: ManagerMediator = manager_mediator
        self.opening_build_complete: bool = False

    def initialise(self) -> None:
        """Set up values that require the bot to be initialised.

        Returns
        -------

        """
        opening: str = self.manager_mediator.manager_request(
            ManagerName.DATA_MANAGER, ManagerRequestType.GET_CHOSEN_OPENING
        )
        self.build_order: list[BuildOrderStep] = self.parse_build_order(
            self.config[BUILDS][opening][OPENING_BUILD_ORDER]
        )

    async def run_build(self) -> None:
        """Run through the opening build till the last step is complete.

        Returns
        -------

        """
        # completed BO normally
        if self.build_step >= len(self.build_order):
            self.opening_build_complete = True
            return

        self.do_step()

    def do_step(self) -> None:
        """Perform the current BuildOrderStep.

         For each BuildOrderStep:
        - check for start condition
        - check if step is active and act accordingly
        - check for end condition

        Returns
        -------

        """
        current_step: BuildOrderStep = self.build_order[self.build_step]
        if self.debug:
            self._draw_current_step(current_step)

        # check if current step can commence
        if current_step.start_condition() and not self.current_step_started:
            self.current_step_started = True

        # current step started and end condition hasn't yet activated
        elif not current_step.end_condition() and self.current_step_started:
            pass

        # command completed, move to next step
        elif current_step.end_condition() and self.current_step_started:
            if current_step.command in self.LOGGING_COMMANDS:
                # supply will always be an int, but python-sc2 has it as a float
                # noinspection PyTypeChecker
                supply_started: int = (
                    self.ai.supply_used
                    if current_step.command not in self.STRUCTURE_COMMANDS
                    else self.ai.supply_used + 1
                )
                logger.info(
                    f"{supply_started} {self.ai.time_formatted} \
                    {current_step.command.name}"
                )
            self.build_step += 1
            self.current_step_started = False

    @staticmethod
    def parse_build_order(raw_build_order: List[str]) -> List[BuildOrderStep]:
        """Convert a build order string to BuildOrderSteps.

        Parameters
        ----------
        raw_build_order :
            Build order as a list of strings where each string is a step.

        Returns
        -------
        List[BuildOrderStep] :
            The parsed build order as BuildOrderSteps that are ready to be run

        """
        build_order: List[BuildOrderStep] = []

        # for step in raw_build_order:
        #     commands: List[str] = step.split(" ")
        #     command: str = commands[0].upper()
        #     target: str = ""
        #
        #     if len(commands) >= 2:
        #         target = commands[-1].upper()
        #
        #     """
        #     Create a BuildOrderStep for each entry in the build order and then append
        #     them to build_order
        #     """

        return build_order

    def complete_step(self) -> None:
        """Manually treat the step as completed.

        This is useful if, for example, a drone gets sniped to adjust and reset the step
        to prevent the opening from getting stuck. You should then handle the missing
        step at some point, such as after the opening is completed.

        Returns
        -------

        """
        self.build_step += 1
        self.current_step_started = False

    async def get_position(
        self, structure_type: UnitID, target: Optional[str]
    ) -> Point2:
        """Convert a position command from the build order to an actual location.

        Examples
        --------
        "hatchery @ nat" :
            ``if structure_type == UnitID.HATCHERY and target == "NAT":``
                ``return self.ai.get_next_expansion()``


        Parameters
        ----------
        structure_type :
            The type of structure to build
        target :
            Where the structure should be built

        Returns
        -------
        Point2 :
            The actual game location where the structure should be built

        """
        raise NotImplementedError

    def _draw_current_step(self, current_step: BuildOrderStep) -> None:
        """Write the current step's command to the screen using debug messages.

        Parameters
        ----------
        current_step :
            BuildOrderStep that's currently being executed

        Returns
        -------

        """
        self.ai.client.debug_text_screen(
            f"OPENING BUILD - Current build step: {str(current_step.command)}",
            pos=(0.2, 0.7),
            size=18,
            color=(0, 255, 255),
        )
