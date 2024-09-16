"""Handle the construction of buildings.

"""
from collections import defaultdict
from typing import (
    TYPE_CHECKING,
    Any,
    Coroutine,
    DefaultDict,
    Dict,
    List,
    Optional,
    Set,
    Union,
)

from cython_extensions import (
    cy_center,
    cy_closest_to,
    cy_distance_to,
    cy_distance_to_squared,
)
from sc2.constants import ALL_GAS
from sc2.data import Race
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId as UnitID
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units

from ares.consts import (
    BUILDING_PURPOSE,
    CREEP_TUMOR_TYPES,
    DEBUG,
    GAS_BUILDINGS,
    ID,
    STRUCTURE_ORDER_COMPLETE,
    TARGET,
    TIME_ORDER_COMMENCED,
    BuildingPurpose,
    ManagerName,
    ManagerRequestType,
    UnitRole,
)
from ares.managers.manager import Manager
from ares.managers.manager_mediator import IManagerMediator, ManagerMediator

if TYPE_CHECKING:
    from ares import AresBot


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

    BUILDING_WORKER_TIMEOUT: float = 120.0

    def __init__(
        self,
        ai: "AresBot",
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
            ManagerRequestType.CANCEL_STRUCTURE: lambda kwargs: (
                self.cancel_structure(**kwargs)
            ),
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
        self._handle_construction_orders()

        # check if a worker has the Building task but isn't being told to build anything
        for worker in self.manager_mediator.get_units_from_role(
            role=UnitRole.BUILDING, unit_type=self.ai.worker_type
        ):
            if worker.tag not in self.building_tracker:
                self.manager_mediator.assign_role(
                    tag=worker.tag, role=UnitRole.GATHERING
                )
                if mfs := self.ai.mineral_field:
                    worker.gather(cy_closest_to(self.ai.start_location, mfs))

    def _handle_construction_orders(self) -> None:
        """Construct tracked buildings.

        Go through the building tracker and control workers. This is to avoid the
        slowing down that happens as a worker approaches the target location when issued
        a 'build' order.

        Returns
        -------

        """
        dead_tags_to_remove: set[int] = set()
        tags_to_remove: set[int] = set()
        structures_dict: dict[
            UnitID, Units
        ] = self.manager_mediator.get_own_structures_dict

        building_spots: set[Point2] = set()

        for worker_tag in self.building_tracker:
            if self.config[DEBUG] and self.building_tracker[worker_tag][TARGET]:
                self.ai.draw_text_on_world(
                    Point2(self.building_tracker[worker_tag][TARGET].position),
                    "BUILDING TARGET",
                )

            structure_id: UnitID = self.building_tracker[worker_tag][ID]

            if (
                self.ai.race != Race.Terran or structure_id == UnitID.REFINERY
            ) and self.ai.time > self.building_tracker[worker_tag][
                TIME_ORDER_COMMENCED
            ] + self.BUILDING_WORKER_TIMEOUT:
                tags_to_remove.add(worker_tag)
                continue

            target: Union[Point2, Unit] = self.building_tracker[worker_tag][TARGET]
            worker = self.ai.unit_tag_dict.get(worker_tag, None)

            if not worker:
                dead_tags_to_remove.add(worker_tag)
                continue

            if worker.is_carrying_resource:
                worker.return_resource()
                continue

            # leave the worker alone
            # TODO: Low health scv could flee in this if block
            if worker.is_constructing_scv:
                continue

            # this happens if no target location is available eg: all expansions taken
            # add a check if multiple workers are using same building spot
            if not target or target in building_spots:
                tags_to_remove.add(worker_tag)
                continue

            building_spots.add(target)

            # check if we are finished with the building worker
            if close_structures := self.ai.structures.filter(
                lambda s: cy_distance_to_squared(s.position, target.position) < 2.0
            ):
                structure: Unit = close_structures[0]
                target_progress: float = 1.0 if self.ai.race == Race.Terran else 1e-16
                if structure.build_progress >= target_progress:
                    tags_to_remove.add(worker_tag)
                    continue

            distance: float = 3.2 if structure_id in GAS_BUILDINGS else 1.0

            # TODO: This is a workaround for a strange bug where the client
            #   returns an error when issuing a build gas command occasionally
            #   this seems to fix it for now
            if self.ai.race == Race.Protoss and structure_id in GAS_BUILDINGS:
                if self.ai.can_afford(structure_id):
                    worker.build_gas(target)
                continue

            # if terran, check for unfinished structure
            existing_unfinished_structure: Optional[Unit] = None
            if self.ai.race == Race.Terran and structure_id in structures_dict:
                if existing_unfinished_structures := [
                    s
                    for s in structures_dict[structure_id]
                    if s.type_id == structure_id
                    and cy_distance_to_squared(s.position, target.position) < 2.25
                    and s.build_progress < 1.0
                ]:
                    existing_unfinished_structure = existing_unfinished_structures[0]
                    distance = 4.5

            if cy_distance_to(worker.position, target.position) > distance:
                order_target: Union[int, Point2, None] = worker.order_target
                point: Point2 = self.manager_mediator.find_path_next_point(
                    start=worker.position,
                    target=target.position,
                    grid=self.manager_mediator.get_ground_grid,
                )
                if (
                    order_target
                    and isinstance(order_target, Point2)
                    and order_target == point
                ):
                    continue
                worker.move(point)

            else:
                if existing_unfinished_structure:
                    worker(AbilityId.SMART, existing_unfinished_structure)
                elif structure_id in GAS_BUILDINGS and self.ai.can_afford(structure_id):
                    # check if target geyser got taken by enemy
                    if self.ai.enemy_structures.filter(
                        lambda u: u.type_id in GAS_BUILDINGS
                        and cy_distance_to_squared(target.position, u.position) < 20.25
                    ):
                        # gas blocked, update with new target and continue
                        # in the next frame worker will try different geyser
                        existing_gas_buildings: Units = self.ai.all_units(GAS_BUILDINGS)
                        if available_geysers := self.ai.vespene_geyser.filter(
                            lambda g: not existing_gas_buildings.closer_than(5.0, g)
                        ):
                            self.building_tracker[worker_tag][
                                TARGET
                            ] = available_geysers.closest_to(self.ai.start_location)
                            continue
                    else:
                        worker.build_gas(target)

                # handle blocked positions
                # TODO: extend this for Zerg
                elif self.ai.race != Race.Zerg and structure_id not in GAS_BUILDINGS:
                    if not self.manager_mediator.can_place_structure(
                        position=target.position, structure_type=structure_id
                    ):
                        self.building_tracker[worker_tag][
                            TARGET
                        ] = self.manager_mediator.request_building_placement(
                            base_location=self.ai.start_location,
                            structure_type=structure_id,
                        )
                        continue

                if (
                    (not worker.is_constructing_scv or worker.is_idle)
                    and self.ai.can_afford(structure_id)
                    and self.ai.tech_requirement_progress(structure_id) == 1.0
                ):
                    worker.build(structure_id, target)

        for tag in tags_to_remove:
            self.building_counter[self.building_tracker[tag][ID]] -= 1
            self.building_tracker.pop(tag, None)
            if tag in self.manager_mediator.get_unit_role_dict[UnitRole.BUILDING]:
                self.manager_mediator.assign_role(tag=tag, role=UnitRole.GATHERING)

        for tag in dead_tags_to_remove:
            position: Point2 = self.building_tracker[tag][TARGET]
            if new_worker := self.manager_mediator.select_worker(
                target_position=position, force_close=True
            ):
                self.building_tracker[new_worker.tag] = self.building_tracker.pop(tag)
                self.manager_mediator.assign_role(
                    tag=new_worker.tag, role=UnitRole.BUILDING
                )

    def cancel_structure(self, structure: Unit) -> None:
        # firstly cancel this structure no matter what
        structure(AbilityId.CANCEL_BUILDINPROGRESS)

        # now look for this structure in the building tracker, and remove it
        structure_id: UnitID = structure.type_id
        worker_tag_to_remove: int = 0
        for worker_tag in self.building_tracker:
            if target := self.building_tracker[worker_tag][TARGET]:
                if [
                    s
                    for s in self.manager_mediator.get_own_structures_dict[structure_id]
                    if cy_distance_to_squared(s.position, target.position) < 4.0
                    and s.build_progress < 1.0
                ]:
                    worker_tag_to_remove = worker_tag
                    break

        # removing unit (worker) from bookkeeping will
        # remove any memory about this structure
        self.remove_unit(worker_tag_to_remove)

    def remove_unit(self, tag: int) -> None:
        """Remove dead units from building tracker.

        Parameters
        ----------
        tag :
            Tag of the unit to remove
        """
        if tag in self.building_tracker:
            self.building_counter[self.building_tracker[tag][ID]] -= 1
            self.building_tracker.pop(tag)
            # ensure worker is correctly reassigned
            self.manager_mediator.assign_role(tag=tag, role=UnitRole.GATHERING)

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
                        lambda mf: cy_distance_to_squared(
                            mf.position, cy_center(possible_geysers)
                        )
                        < 144.0
                    ):
                        target_geyser: Unit = cy_closest_to(
                            cy_center(close_mf), possible_geysers
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

    def build_with_specific_worker(
        self,
        worker: Unit,
        structure_type: UnitID,
        pos: Point2,
        assign_role: bool = True,
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
        assign_role :
            Auto assign BUILDING UnitRole?
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

        tag: int = worker.tag
        if tag not in self.building_tracker:
            self.building_tracker[tag] = {
                ID: structure_type,
                TARGET: pos,
                TIME_ORDER_COMMENCED: self.ai.time,
                BUILDING_PURPOSE: building_purpose,
                STRUCTURE_ORDER_COMPLETE: True,
            }

            self.building_counter[self.building_tracker[tag][ID]] += 1
            if assign_role:
                self.manager_mediator.assign_role(tag=tag, role=UnitRole.BUILDING)
            return True
        return False

    @staticmethod
    async def on_structure_took_damage(structure: Unit) -> None:
        """Actions to take if a structure is under attack.

        Parameters
        ----------
        structure :
            The structure that took damage.
        """
        if structure.type_id in CREEP_TUMOR_TYPES:
            return

        compare_health: float = max(50.0, structure.health_max * 0.09)
        if structure.health < compare_health:
            structure(AbilityId.CANCEL_BUILDINPROGRESS)
