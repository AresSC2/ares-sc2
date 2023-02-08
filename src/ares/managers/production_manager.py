"""Handle production.

"""
from typing import Any, Dict, List

from consts import DEBUG, UNITS_TO_IGNORE, ManagerName, ManagerRequestType
from custom_bot_ai import CustomBotAI
from managers.build_runner import BuildRunner
from managers.manager import Manager
from managers.manager_mediator import IManagerMediator, ManagerMediator
from production.base_production import BaseProduction
from sc2.ids.unit_typeid import UnitTypeId as UnitID
from sc2.position import Point2
from sc2.units import Units


class ProductionManager(Manager, IManagerMediator):
    """Where all production is managed."""

    def __init__(
        self,
        ai: CustomBotAI,
        config: Dict,
        mediator: ManagerMediator,
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
        super().__init__(ai, config, mediator)

        self.main_building_location: Point2 = self.ai.start_location
        self.debug: bool = config[DEBUG]

        # production classes

        self.build_runner: BuildRunner = BuildRunner(
            ai,
            config,
            mediator,
        )

        self.production_facilities: List[BaseProduction] = []

    def manager_request(
        self,
        receiver: ManagerName,
        request: ManagerRequestType,
        reason: str = None,
        **kwargs
    ) -> Any:
        """Enables ManagerRequests to this Manager.

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
        return self.manager_requests_dict[request](kwargs)

    async def update(self, iteration: int) -> None:
        """Handle production.

        Parameters
        ----------
        iteration :
            The game iteration.

        Returns
        -------

        """

        if not self.build_runner.opening_build_complete:
            await self.build_runner.run_build()

        else:
            # check where we place tech structures
            if iteration % 16 == 0:
                self._check_main_building_location()

            for facility in self.production_facilities:
                await facility.update(
                    self.manager_mediator.get_bot_mode,
                    self.main_building_location,
                    iteration,
                )

    async def initialise(self) -> None:
        """Set up values that require the bot to be initialised.

        Returns
        -------

        """
        self.build_runner.initialise()

    def _check_main_building_location(self) -> None:
        """Select a townhall to place buildings near.

        Returns
        -------

        """
        # check if enemy units are close to current building location
        enemy_close_to_loc: Units = self.ai.enemy_units.filter(
            lambda u: u.type_id not in UNITS_TO_IGNORE
            and u.distance_to(self.main_building_location) < 22.0
        )
        if self.ai.get_total_supply(enemy_close_to_loc) > 1.0:
            ths: Units = self.ai.townhalls.filter(
                lambda th: not self.ai.mineral_field(
                    {UnitID.RICHMINERALFIELD, UnitID.RICHMINERALFIELD750}
                ).closer_than(20, th.position)
            )
            if ths:
                self.main_building_location = ths.furthest_to(
                    enemy_close_to_loc.center
                ).position
            # rare: no townhalls ready
            else:
                self.main_building_location = self.ai.game_info.map_center
