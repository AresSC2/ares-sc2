"""Handle the construction of buildings.

"""
from collections import defaultdict
from typing import Any, Coroutine, DefaultDict, Dict, List, Optional, Set, Union

from sc2.constants import ALL_GAS
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId as UnitID
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units

from consts import (
    BUILDING,
    BUILDING_PURPOSE,
    CANCEL_ORDER,
    CREEP_TUMOR_TYPES,
    DEBUG,
    GAS_BUILDINGS,
    ID,
    TARGET,
    TIME_ORDER_COMMENCED,
    BotMode,
    BuildingPurpose,
    ManagerName,
    ManagerRequestType,
    UnitRole,
)
from custom_bot_ai import CustomBotAI
from managers.manager import Manager
from managers.manager_mediator import IManagerMediator, ManagerMediator


class BuildingManager(Manager, IManagerMediator):
    """Handle the construction of buildings.

    Attributes
    ----------
    blocked_expansion_locations : Set[Point2]
        Which expansion locations are blocked and not considered for expanding
    building_tracker : Dict[int, Dict[str, Union[Point2, Unit, UnitID], float]
        Tracks the worker tag to:
            UnitID of the building to be built
            Point2 of where the building is to be placed
            In-game time when the order started
            Why the building is being built
    building_counter : DefaultDict[UnitID, int]
        Tracks the type of building in the tracker and how many are present

    """

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
        super(BuildingManager, self).__init__(ai, config, mediator)

        self.manager_requests_dict = {
            ManagerRequestType.GET_BUILDING_COUNTER: lambda kwargs: (
                self.building_counter
            ),
            ManagerRequestType.GET_BUILDING_TRACKER_DICT: lambda kwargs: (
                self.building_tracker
            ),
            ManagerRequestType.BUILD_WITH_SPECIFIC_WORKER: lambda kwargs: (
                self.build_with_specific_worker(**kwargs)
            ),
        }

        self.building_tracker: Dict[
            int, Dict[str, Union[Point2, Unit, UnitID], float]
        ] = dict()
        self.building_counter: DefaultDict[UnitID, int] = defaultdict(int)
        # remember for each expansion attempt, otherwise we lose memory
        # should be cleared after expanding
        self.blocked_expansion_locations: Set[Point2] = set()

    def manager_request(
        self,
        receiver: ManagerName,
        request: ManagerRequestType,
        reason: str = None,
        **kwargs,
    ) -> Optional[Union[Dict, DefaultDict, Coroutine[Any, Any, bool]]]:
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
        """Update trackers and handle construction of buildings.

        Parameters
        ----------
        iteration :
            The current game iteration.

        Returns
        -------

        """
        self.building_counter = defaultdict(int)
        for tag in self.building_tracker:
            self.building_counter[self.building_tracker[tag][ID]] += 1

        await self._handle_construction_orders(self.manager_mediator.get_bot_mode)

        # check if a worker has the Building task but isn't being told to build anything
        # this normally occurs if the building gets canceled
        for worker in self.manager_mediator.get_units_from_role(
            role=UnitRole.BUILDING, unit_type=self.ai.worker_type
        ):
            if worker.tag not in self.building_tracker:
                self.manager_mediator.assign_role(
                    tag=worker.tag, role=UnitRole.GATHERING
                )

    async def _handle_construction_orders(self, _bot_mode: BotMode) -> None:
        """Construct tracked buildings.

        Go through the building tracker and control workers. This is to avoid the
        slowing down that happens as a worker approaches the target location when issued
        a 'build' order.

        Parameters
        ----------
        _bot_mode :
            What mode the bot is in (unused)

        Returns
        -------

        """
        tags_to_remove: Set[int] = set()
        for worker_tag in self.building_tracker:
            if self.config[DEBUG] and self.building_tracker[worker_tag][TARGET]:
                self.ai.draw_text_on_world(
                    Point2(self.building_tracker[worker_tag][TARGET].position),
                    "BUILDING TARGET",
                )
            # check if building is morphing
            worker = self.ai.units.by_tag(worker_tag)

            structure_id: UnitID = self.building_tracker[worker_tag][ID]
            target: Point2 = self.building_tracker[worker_tag][TARGET]

            # check if an order has been stuck in the building tracker for too long
            if (
                self.ai.time
                > self.building_tracker[worker_tag][TIME_ORDER_COMMENCED]
                + self.config[BUILDING][CANCEL_ORDER]
            ):
                tags_to_remove.add(worker_tag)
                continue

            # this happens if no target location is available eg: all expansions taken
            if not target:
                tags_to_remove.add(worker_tag)
                continue

            # TODO: find the maximum distance so we don't have to keep adjusting this
            distance: float = 3.2 if structure_id in GAS_BUILDINGS else 1.0

            # rasper: I put this here to build right away, because it bugs out sometimes
            # if trying to path
            # TODO: fix this so worker paths to building
            if structure_id in GAS_BUILDINGS:
                worker.build_gas(target)

            elif worker.distance_to(target) > distance:
                point: Point2 = self.manager_mediator.find_path_next_point(
                    start=worker.position,
                    target=target.position,
                    grid=self.manager_mediator.get_ground_grid,
                )
                worker.move(point)

            else:
                if self.ai.can_afford(structure_id):
                    worker.build(structure_id, target)

        for tag in tags_to_remove:
            self.building_tracker.pop(tag, None)

    def remove_unit(self, tag: int) -> None:
        """Remove dead units from building tracker.

        Parameters
        ----------
        tag :
            Tag of the unit to remove

        Returns
        -------

        """
        self.building_tracker.pop(tag, None)

    async def construct_gas(
        self, max_building: int = 1, geyser: Optional[Unit] = None
    ) -> None:
        """Build a gas building.

        Gas buildings are constructed differently than other buildings so this function
        needs to be used.

        Parameters
        ----------
        max_building :
            Maximum amount of gas buildings that can be built at once
        geyser :
            The geyser to build the gas building on

        Returns
        -------

        """
        pending_geysers: List[Unit] = [
            self.building_tracker[tag][TARGET]
            for tag in self.building_tracker
            if self.building_tracker[tag][ID] == self.ai.gas_type
        ]
        building_gases: Units = self.manager_mediator.get_own_structures_dict[
            self.ai.gas_type
        ].filter(lambda g: g.build_progress < 1.0)

        if len(pending_geysers) + len(building_gases) >= max_building:
            return

        target_geyser: Optional[Unit] = None

        if geyser:
            target_geyser = geyser
        else:
            existing_gas_buildings: Units = self.ai.all_units(ALL_GAS)

            th: Unit
            progress: float = 0.55 if self.ai.time > 300 else 0.98
            for th in self.ai.townhalls:
                if th.build_progress < progress:
                    continue
                # early game only take gas at spawn or natural
                if self.ai.time < 260 and (
                    th.distance_to(self.ai.start_location) > 10
                    and th.distance_to(self.manager_mediator.get_own_nat) > 10
                ):
                    continue

                possible_geysers: Units = Units([], self.ai)

                for geyser in self.ai.vespene_geyser.closer_than(15, th.position):
                    if (
                        existing_gas_buildings
                        and existing_gas_buildings.closer_than(
                            1, geyser.position
                        ).exists
                        or geyser in pending_geysers
                    ):
                        continue

                    possible_geysers.append(geyser)

                if possible_geysers.amount == 0:
                    continue

                if self.ai.time > 300:
                    target_geyser: Unit = possible_geysers.first

                else:
                    # target geyser closest to mf so worker doesn't have to move as far
                    if close_mf := self.ai.mineral_field.filter(
                        lambda mf: mf.distance_to(possible_geysers.center) < 12.0
                    ):
                        target_geyser: Unit = possible_geysers.closest_to(
                            close_mf.center
                        )
                    else:
                        target_geyser: Unit = possible_geysers.first
                # found a geyser so break out the loop
                break

        if target_geyser:
            worker: Unit = self.manager_mediator.select_worker(
                target_position=target_geyser.position, force_close=True
            )
            if worker:
                worker.move(target_geyser.position)
                self.building_tracker[worker.tag] = {
                    ID: self.ai.gas_type,
                    TARGET: target_geyser,
                    TIME_ORDER_COMMENCED: self.ai.time,
                    BUILDING_PURPOSE: BuildingPurpose.NORMAL_BUILDING,
                }
                pending_geysers.append(target_geyser)
                self.manager_mediator.assign_role(
                    tag=worker.tag, role=UnitRole.BUILDING
                )

    def is_pending(self, structure_type: UnitID, simul_amount: int):
        """See how many structure_type buildings are being tracked.

        Parameters
        ----------
        structure_type :
            The type of structure to look for
        simul_amount :
            Amount of buildings that can be built at once.

        Examples
        --------
        ``is_pending(UnitID.BARRACKS, 2)``

        This will return False if only one Barracks is in progress/tracked since 2
        are allowed to be built simultaneously.

        Returns
        -------
        bool :
            False if the number of buildings under construction is less than the
            allowed simultaneous amount, otherwise True

        """
        if (
            structure_type not in self.building_counter
            or self.building_counter[structure_type] < simul_amount
        ):
            return False
        return True

    async def find_valid_position(
        self, building: UnitID, pos: Point2
    ) -> Union[Point2, Coroutine[Any, Any, Optional[Point2]]]:
        """Make sure multiple workers aren't trying to build in the same position.

        Notes
        -----
            This can potentially result in building in a location inside the main base
            that will create a wall.

        Parameters
        ----------
        building
        pos

        Returns
        -------
        Union[Point2, Coroutine[Any, Any, Optional[Point2]]] :
            Either a Point2 that's a valid placement or a position in the main base.

        """
        # find a new location near the old one
        new_pos: Point2 = await self.ai.find_placement(
            building, pos.towards(self.ai.game_info.map_center, 7), max_distance=10
        )
        if new_pos:
            return new_pos
        else:
            return self.ai.townhalls[0].position.towards_with_random_angle(
                self.ai.game_info.map_center, 10
            )

    async def build_with_specific_worker(
        self,
        worker: Unit,
        structure_type: UnitID,
        pos: Point2,
        building_purpose: BuildingPurpose = BuildingPurpose.NORMAL_BUILDING,
    ) -> bool:
        """Other classes may call this to have a specific worker build a structure.

        Parameters
        ----------
        worker :
            The chosen worker.
        structure_type :
            What type of structure to build.
        pos :
            Where the structure should be placed.
        building_purpose :
            Why the structure is being placed.

        Returns
        -------
        bool :
            True if a position for the building is found and the worker is valid,
            otherwise False

        """
        if not pos or not worker:
            return False

        final_pos: Optional[Point2] = await self.ai.find_placement(
            building=structure_type,
            near=pos,
            max_distance=3,
            random_alternative=False,
            placement_step=1,
        )
        if not final_pos:
            return False

        self.building_tracker[worker.tag] = {
            ID: structure_type,
            TARGET: final_pos,
            TIME_ORDER_COMMENCED: self.ai.time,
            BUILDING_PURPOSE: building_purpose,
        }
        self.manager_mediator.assign_role(tag=worker.tag, role=UnitRole.BUILDING)
        return True

    @staticmethod
    async def on_structure_took_damage(structure: Unit) -> None:
        """Actions to take if a structure is under attack.

        Parameters
        ----------
        structure :
            The structure that took damage.

        Returns
        -------

        """
        if structure.type_id in CREEP_TUMOR_TYPES:
            return

        compare_health: float = max(50.0, structure.health_max * 0.09)
        if structure.health < compare_health:
            structure(AbilityId.CANCEL_BUILDINPROGRESS)
