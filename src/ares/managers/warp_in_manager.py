from typing import TYPE_CHECKING, Any, Coroutine, DefaultDict, Optional, Union

from cython_extensions.geometry import cy_distance_to_squared
from loguru import logger
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId as UnitID
from sc2.position import Point2
from sc2.unit import Unit

from ares.consts import ManagerName, ManagerRequestType
from ares.managers.manager import Manager
from ares.managers.manager_mediator import IManagerMediator, ManagerMediator

if TYPE_CHECKING:
    from ares import AresBot


class WarpInManager(Manager, IManagerMediator):
    PSIONIC_MATRIX_RANGE_PRISM: float = 3.75

    def __init__(
        self,
        ai: "AresBot",
        config: dict,
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
        """
        super(WarpInManager, self).__init__(ai, config, mediator)

        self.manager_requests_dict = {
            ManagerRequestType.REQUEST_WARP_IN: lambda kwargs: (
                self.request_warp_in(**kwargs)
            ),
        }

        self.warp_in_positions: set[Point2] = set()
        self.requested_warp_ins: list[(UnitID, Point2)] = []

    def manager_request(
        self,
        receiver: ManagerName,
        request: ManagerRequestType,
        reason: str = None,
        **kwargs,
    ) -> Optional[Union[dict, DefaultDict, Coroutine[Any, Any, bool]]]:
        """Fetch information from this Manager so another Manager can use it.

        Parameters
        ----------
        receiver :
            This Manager.
        request :
            What kind of request is being made
        reason :
            Why the reason is being made
        kwargs :
            Additional keyword args if needed for the specific request, as determined
            by the function signature (if appropriate)

        Returns
        -------
        Optional[Union[Dict, DefaultDict, Coroutine[Any, Any, bool]]] :
            Everything that could possibly be returned from the Manager fits in there

        """
        return self.manager_requests_dict[request](kwargs)

    async def update(self, iteration: int) -> None:
        """Update worker on route

        Bookkeeping is also updated via `on_unit_destroyed` and `on_building_started`.

        Parameters
        ----------
        iteration :
            The current game iteration.

        """
        self.warp_in_positions = set()
        self.requested_warp_ins = []

    def request_warp_in(
        self, build_from: UnitID, unit_type: UnitID, target: Optional[Point2]
    ) -> None:
        """
        Get a warp in spot closest to target
        This is intended as a simulated alternative to example:
        `await self.find_placement(AbilityId.WARPGATETRAIN_ZEALOT, position)`
        So prevents making query to the game client.

        Parameters
        ----------
        build_from
        unit_type
        target

        Returns
        -------

        """
        if not target:
            target = self.ai.start_location

        self.requested_warp_ins.append((build_from, unit_type, target))

    async def do_warp_ins(self) -> None:
        if not self.requested_warp_ins:
            return
        power_sources: list[Unit] = (
            self.manager_mediator.get_own_structures_dict[UnitID.PYLON]
            + self.manager_mediator.get_own_army_dict[UnitID.WARPPRISMPHASING]
        )
        if not power_sources:
            logger.warning("Requesting warp in spot, but no power sources found")
            return

        for build_from, unit_type, target in self.requested_warp_ins:

            sorted_power_sources = sorted(
                power_sources, key=lambda x: cy_distance_to_squared(x.position, target)
            )
            for power_source in sorted_power_sources:
                if AbilityId.WARPGATETRAIN_STALKER in build_from.abilities:
                    placement = await self.ai.find_placement(
                        AbilityId.WARPGATETRAIN_STALKER,
                        power_source.position,
                        placement_step=1,
                    )
                    if placement is None:
                        # return ActionResult.CantFindPlacementLocation
                        logger.info(f"Can't find placement for {unit_type}")
                        return
                    build_from.warp_in(unit_type, placement)
                    break
