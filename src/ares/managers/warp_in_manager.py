from math import ceil
from typing import TYPE_CHECKING, Any, Coroutine, DefaultDict, Optional, Union

import numpy as np
from cython_extensions import (
    cy_can_place_structure,
    cy_distance_to_squared,
    cy_pylon_matrix_covers,
    cy_sorted_by_distance_to,
)
from loguru import logger
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId as UnitID
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units

from ares.consts import ManagerName, ManagerRequestType, UnitTreeQueryType
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
            size = (2, 2) if unit_type == UnitID.STALKER else (1, 1)
            power_sources = cy_sorted_by_distance_to(power_sources, target)
            for power_source in power_sources:
                type_id: UnitID = power_source.type_id
                if type_id == UnitID.PYLON:
                    half_psionic_range = 3
                else:
                    half_psionic_range = ceil(self.PSIONIC_MATRIX_RANGE_PRISM / 2)
                power_source_pos: Point2 = power_source.position

                positions: list[Point2] = [
                    Point2((power_source_pos.x + x, power_source_pos.y + y))
                    for x in range(-half_psionic_range, half_psionic_range + 1)
                    for y in range(-half_psionic_range, half_psionic_range + 1)
                    if Point2((power_source_pos.x + x, power_source_pos.y + y))
                    not in self.warp_in_positions
                ]

                in_range: list[Units] = self.manager_mediator.get_units_in_range(
                    start_points=positions,
                    distances=1.75,
                    query_tree=UnitTreeQueryType.AllOwn,
                )

                for i, pos in enumerate(positions):
                    if pos in self.warp_in_positions:
                        continue

                    if [
                        u
                        for u in in_range[i]
                        if cy_distance_to_squared(u.position, pos) < 2.25
                        and not u.is_flying
                    ]:
                        continue

                    if cy_can_place_structure(
                        (int(pos.x), int(pos.y)),
                        size,
                        self.ai.state.creep.data_numpy,
                        self.ai.game_info.placement_grid.data_numpy,
                        self.manager_mediator.get_ground_grid.astype(np.uint8).T,
                        avoid_creep=True,
                        include_addon=False,
                    ) and cy_pylon_matrix_covers(
                        pos,
                        power_sources,
                        self.ai.game_info.terrain_height.data_numpy,
                        pylon_build_progress=1.0,
                    ):
                        ability: AbilityId = (
                            AbilityId.WARPGATETRAIN_STALKER
                            if unit_type == UnitID.STALKER
                            else AbilityId.WARPGATETRAIN_ZEALOT
                        )
                        pos = await self.ai.find_placement(ability, pos)
                        self.warp_in_positions.add(pos)
                        build_from.warp_in(unit_type, pos)
                        self.warp_in_positions.add(pos)
                        if unit_type == UnitID.STALKER:
                            for p in pos.neighbors8:
                                self.warp_in_positions.add(p)
