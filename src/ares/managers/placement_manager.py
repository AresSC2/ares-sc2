import time
from itertools import product
from os import getcwd, path
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Coroutine,
    DefaultDict,
    FrozenSet,
    Optional,
    Union,
)

import numpy as np
from cython_extensions import (
    cy_can_place_structure,
    cy_distance_to_squared,
    cy_find_building_locations,
    cy_get_bounding_box,
    cy_pylon_matrix_covers,
    cy_towards,
)
from loguru import logger
from sc2.constants import ALL_GAS
from sc2.data import Race
from sc2.ids.unit_typeid import UnitTypeId as UnitID
from sc2.position import Point2, Point3
from sc2.unit import Unit
from sc2.units import Units

from ares.config_parser import ConfigParser
from ares.consts import (
    BUILDING_PLACEMENTS,
    DEBUG,
    DEBUG_OPTIONS,
    GAS_BUILDINGS,
    PLACEMENT,
    SHOW_BUILDING_FORMATION,
    WORKER_ON_ROUTE_TIMEOUT,
    BuildingPlacementOptions,
    BuildingSize,
    ManagerName,
    ManagerRequestType,
)
from ares.dicts.structure_to_building_size import STRUCTURE_TO_BUILDING_SIZE
from ares.managers.manager import Manager
from ares.managers.manager_mediator import IManagerMediator, ManagerMediator

if TYPE_CHECKING:
    from ares import AresBot


class PlacementManager(Manager, IManagerMediator):
    """Handle the placements of buildings.

    Attributes
    ----------
    placements_dict : dict[Point2 : dict[BuildingSize:dict]]
        Dictionary containing 2x2 and 3x3 placement formation,
        for every expansion location on the map.
    points_to_avoid_grid : np.ndarray
        Array of whole map, where a 1 indicates a position should be avoided,
        when calculating placements.
    race_to_building_solver_method : Callable
        Method to call on_game_start when solving placement formation.
    structure_tag_to_base_location :
        For convenience, this allows faster lookup of placements_dict.
    """

    creep_grid: np.ndarray
    placement_grid: np.ndarray
    pathing_grid: np.ndarray
    points_to_avoid_grid: np.ndarray
    BUILDING_SIZE_ENUM_TO_TUPLE: dict[BuildingSize, tuple[int, int]] = {
        BuildingSize.FIVE_BY_FIVE: (5, 5),
        BuildingSize.THREE_BY_THREE: (3, 3),
        BuildingSize.TWO_BY_TWO: (2, 2),
    }
    BUILDING_SIZE_ENUM_TO_RADIUS: dict[BuildingSize, float] = {
        BuildingSize.FIVE_BY_FIVE: 2.5,
        BuildingSize.THREE_BY_THREE: 1.5,
        BuildingSize.TWO_BY_TWO: 1.0,
    }
    UNBUILDABLES: set[UnitID] = {
        UnitID.UNBUILDABLEPLATESDESTRUCTIBLE,
        UnitID.UNBUILDABLEBRICKSDESTRUCTIBLE,
        UnitID.UNBUILDABLEROCKSDESTRUCTIBLE,
    }

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
        super(PlacementManager, self).__init__(ai, config, mediator)

        self.manager_requests_dict = {
            ManagerRequestType.CAN_PLACE_STRUCTURE: lambda kwargs: (
                self.can_place_structure(**kwargs)
            ),
            ManagerRequestType.GET_PLACEMENTS_DICT: lambda kwargs: (
                self.placements_dict
            ),
            ManagerRequestType.GET_PVZ_NAT_GATEKEEPER_POS: lambda kwargs: (
                self._pvz_nat_gatekeeper_pos
            ),
            ManagerRequestType.REQUEST_BUILDING_PLACEMENT: lambda kwargs: (
                self.request_building_placement(**kwargs)
            ),
        }

        # main dict where all data is organised
        # {base_loc: 3x3: {building_pos: (2, 2), taken: False, is_wall: True}, {...}
        #            2x2: {building_pos: (5, 5), taken: True, is_wall: False}, {...}}
        self.placements_dict: dict[Point2, dict[BuildingSize, dict]] = dict()
        self.race_to_building_solver_method: dict[Race, Callable] = {
            Race.Terran: lambda: self._solve_terran_building_formation(),
            Race.Protoss: lambda: self._solve_protoss_building_formation(),
            Race.Zerg: lambda: self._solve_zerg_building_formation(),
        }
        # this is to allow faster lookup of placements_dict
        self.structure_tag_to_base_location: dict[int, Point2] = dict()
        # this prevents iterating through all bases to check workers on route
        # key: Unique placement location, value: main base location
        self.worker_on_route_tracker: dict[Point2, Point2] = dict()
        self.WORKER_ON_ROUTE_TIMEOUT: float = self.config[PLACEMENT][
            WORKER_ON_ROUTE_TIMEOUT
        ]

        __ares_config_location__: str = path.realpath(
            path.join(getcwd(), path.dirname(__file__), "..")
        )
        self.__user_config_location__: str = path.abspath(".")
        config_parser: ConfigParser = ConfigParser(
            __ares_config_location__, self.__user_config_location__, BUILDING_PLACEMENTS
        )

        self._user_placements: dict = config_parser.parse()
        self._pvz_nat_gatekeeper_pos: Optional[Point2] = None

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
        if self.ai.arcade_mode:
            return

        self.warp_in_positions = set()
        self.requested_warp_ins = []
        # occasionally check if worker on route locations can be unlocked
        if iteration % 16 == 0 and len(self.worker_on_route_tracker) > 0:
            self._track_requested_placements()

        if self.config[DEBUG] and self.config[DEBUG_OPTIONS][SHOW_BUILDING_FORMATION]:
            await self._draw_building_placements()

    def initialise(self) -> None:
        """Calculate building formations on game commencement."""
        if self.ai.arcade_mode:
            return
        start: float = time.time()
        self.points_to_avoid_grid = np.zeros(
            self.ai.game_info.placement_grid.data_numpy.shape, dtype=np.uint8
        )
        self.creep_grid = self.ai.state.creep.data_numpy
        self.placement_grid = self.ai.game_info.placement_grid.data_numpy
        # Note: use MapAnalyzers pathing grid to get rocks etc
        self.pathing_grid = self.manager_mediator.get_ground_grid.astype(np.uint8).T
        for destructible in self.ai.destructables:
            if destructible.type_id in self.UNBUILDABLES:
                pos: Point2 = destructible.position
                start_x: int = int(pos.x - 1)
                start_y: int = int(pos.y - 1)
                self.points_to_avoid_grid[
                    start_y : start_y + 2, start_x : start_x + 2
                ] = 1
        # before doing any automated placement formation, add user placements
        self._extract_user_placements()
        self.race_to_building_solver_method[self.ai.race]()
        finish: float = time.time()

        logger.info(f"Solved placement formation in {(finish - start)*1000} ms")

    def can_place_structure(
        self, position: Point2, structure_type: UnitID, include_addon: bool = False
    ) -> bool:
        """Check if structure can be placed at a given position.

        Faster cython alternative to `python-sc2` `await self.can_place()`

        Parameters
        ----------
        position : Point2
            The intended building position.
        structure_type : UnitID
            Structure we are trying to place.
        include_addon : bool, optional
            For Terran structures, check addon will place too.

        Returns
        ----------
        bool :
            Indicating if structure can be placed at given position.
        """
        assert structure_type in STRUCTURE_TO_BUILDING_SIZE, (
            f"{structure_type}, " f"not present in STRUCTURE_TO_BUILDING_SIZE dict"
        )

        if structure_type in GAS_BUILDINGS:
            pos: Point2 = position.position
            existing_gas_buildings: Units = self.ai.all_units.filter(
                lambda u: u.type_id in ALL_GAS
                and cy_distance_to_squared(pos, u.position) < 12.25
            )
            return len(existing_gas_buildings) == 0

        size: BuildingSize = STRUCTURE_TO_BUILDING_SIZE[structure_type]
        offset: float = self.BUILDING_SIZE_ENUM_TO_RADIUS[size]
        origin_x: int = int(position[0] - offset)
        origin_y: int = int(position[1] - offset)

        size: tuple[int, int] = self.BUILDING_SIZE_ENUM_TO_TUPLE[size]
        return cy_can_place_structure(
            (origin_x, origin_y),
            size,
            self.ai.state.creep.data_numpy,
            self.ai.game_info.placement_grid.data_numpy,
            self.manager_mediator.get_ground_grid.astype(np.uint8).T,
            avoid_creep=self.ai.race != Race.Zerg,
            include_addon=include_addon,
        )

    def request_building_placement(
        self,
        base_location: Point2,
        structure_type: UnitID,
        first_pylon: bool = False,
        static_defence: bool = False,
        wall: bool = False,
        find_alternative: bool = True,
        reserve_placement: bool = True,
        within_psionic_matrix: bool = False,
        pylon_build_progress: float = 1.0,
        closest_to: Optional[Point2] = None,
    ) -> Optional[Point2]:
        """Given a base location and building size find an available placement.

        Parameters
        ----------
        base_location : Point2
            The general area where the placement should be near.
            This should be a expansion location.
        structure_type : UnitID
            Structure type requested.
        first_pylon : bool (default=False)
            Try to take designated first pylon if available.
        static_defence : bool (default=False)
            Try to take designated static defence placements if available.
        wall : bool (default=False)
            Request a wall structure placement.
            Will find alternative if no wall placements available.
        find_alternative : bool (default=True)
            If no placements available at base_location, find
            alternative at nearby base.
        reserve_placement : bool (default=True)
            Reserve this booking for a while, so another customer doesn't
            request it.
        within_psionic_matrix : bool (default=False)
            Protoss specific -> calculated position have power?
        pylon_build_progress : float (default=1.0)
            Only relevant if `within_psionic_matrix = True`
        closest_to : Point2, optional
            Find placement at base closest to this

        Returns
        ----------
        bool :
            Indicating if structure can be placed at given position.

        """
        assert (
            self.ai.race != Race.Zerg
        ), "`request_building_placement` not supported for Zerg"
        assert (
            structure_type in STRUCTURE_TO_BUILDING_SIZE
        ), f"{structure_type} not found in STRUCTURE_TO_BUILDING_SIZE dict"

        base_locations: set[Point2] = set(self.placements_dict.keys())
        building_size: BuildingSize = STRUCTURE_TO_BUILDING_SIZE[structure_type]
        # find base location in placements_dict, or find closest
        location: Point2 = (
            base_location
            if base_location in self.placements_dict
            else min(
                base_locations,
                key=lambda k: cy_distance_to_squared(k, base_location),
            )
        )

        building_at_base: Point2 = location
        if building_size in self.placements_dict[location]:
            available: list[Point2] = self._find_potential_placements_at_base(
                building_size,
                location,
                structure_type,
                within_psionic_matrix,
                pylon_build_progress,
            )

            # don't steal static def positions
            if structure_type == UnitID.PYLON:
                available = [
                    a
                    for a in available
                    if not self.placements_dict[location][building_size][a][
                        "static_defence"
                    ]
                ]

            # no available placements at base_location
            if len(available) == 0:
                if not find_alternative:
                    logger.warning(
                        f"No available {building_size} found near location:"
                        f" {base_location}"
                    )
                    return
                base_locations.remove(location)
                locations = sorted(
                    base_locations,
                    key=lambda k: cy_distance_to_squared(k, base_location),
                )
                for location in locations:
                    available: list[Point2] = self._find_potential_placements_at_base(
                        building_size, location, structure_type, within_psionic_matrix
                    )
                    if len(available) > 0:
                        building_at_base = location
                        break

            if len(available) == 0:
                if self.ai.time > 60.0:
                    logger.info(
                        f"{self.ai.time_formatted}: No available {building_size}"
                        f" found anywhere on map, giving up."
                    )
                return

            # we have some available positions, calculate the final placement

            # if we require power
            if within_psionic_matrix:
                build_near: Point2 = building_at_base
                two_by_twos: dict = self.placements_dict[building_at_base][
                    BuildingSize.TWO_BY_TWO
                ]
                # build near optimal pylon, if we don't have too much there
                if optimal_pylon := [
                    a
                    for a in two_by_twos
                    if self.placements_dict[building_at_base][BuildingSize.TWO_BY_TWO][
                        a
                    ]["optimal_pylon"]
                ]:
                    potential_build_near: Point2 = optimal_pylon[0]
                    three_by_threes: dict = self.placements_dict[building_at_base][
                        BuildingSize.THREE_BY_THREE
                    ]
                    close_to_pylon: list[Point2] = [
                        p
                        for p in three_by_threes
                        if cy_distance_to_squared(p, potential_build_near) < 42.25
                    ]
                    if len(close_to_pylon) < 4:
                        build_near = optimal_pylon[0]
                closest_to: Point2 = (
                    base_location if not wall else self.ai.main_base_ramp.bottom_center
                )
                final_placement = self._find_placement_near_pylon(
                    available, build_near, pylon_build_progress, closest_to
                )
                if not final_placement:
                    logger.warning(
                        f"Can't find placement near pylon near {building_at_base}."
                    )
                    return
            # don't need power, all other options
            else:
                # let this block be the default placement
                if not closest_to:
                    final_placement: Point2 = min(
                        available,
                        key=lambda k: cy_distance_to_squared(k, building_at_base),
                    )
                else:
                    final_placement: Point2 = min(
                        available, key=lambda k: cy_distance_to_squared(k, closest_to)
                    )
                # Now in this block, see if we want to specialize final_placement
                # First Pylon
                if first_pylon and (
                    available_first_pylon := [
                        a
                        for a in available
                        if self.placements_dict[building_at_base][building_size][a][
                            "first_pylon"
                        ]
                    ]
                ):
                    final_placement = min(
                        available_first_pylon,
                        key=lambda k: cy_distance_to_squared(k, building_at_base),
                    )

                # At wall
                elif wall:
                    if available_wall := [
                        a
                        for a in available
                        if self.placements_dict[building_at_base][building_size][a][
                            "is_wall"
                        ]
                    ]:
                        final_placement = min(
                            available_wall,
                            key=lambda k: cy_distance_to_squared(
                                k, self.ai.main_base_ramp.bottom_center
                            ),
                        )
                    else:
                        final_placement = min(
                            available,
                            key=lambda k: cy_distance_to_squared(
                                k, self.ai.main_base_ramp.bottom_center
                            ),
                        )

                # Static Defence
                elif static_defence and (
                    available_static_defence := [
                        a
                        for a in available
                        if self.placements_dict[building_at_base][building_size][a][
                            "static_defence"
                        ]
                    ]
                ):
                    final_placement = min(
                        available_static_defence,
                        key=lambda k: cy_distance_to_squared(k, building_at_base),
                    )

                # Optimal Pylon
                elif structure_type == UnitID.PYLON and (
                    available_opt := [
                        a
                        for a in available
                        if self.placements_dict[building_at_base][building_size][a][
                            "optimal_pylon"
                        ]
                    ]
                ):
                    final_placement = min(
                        available_opt,
                        key=lambda k: cy_distance_to_squared(k, building_at_base),
                    )

                # prod pylons
                elif available_prod := [
                    a
                    for a in available
                    if self.placements_dict[building_at_base][building_size][a][
                        "production_pylon"
                    ]
                ]:
                    final_placement = min(
                        available_prod,
                        key=lambda k: cy_distance_to_squared(k, building_at_base),
                    )

            if reserve_placement:
                self.worker_on_route_tracker[final_placement] = building_at_base
                potential_placements: dict[Point2:dict] = self.placements_dict[
                    building_at_base
                ][building_size]
                potential_placements[final_placement]["worker_on_route"] = True
                potential_placements[final_placement]["time_requested"] = self.ai.time

            return final_placement

        else:
            logger.warning(f"No {building_size} present in placement bookkeeping.")

    def _extract_user_placements(self) -> None:
        if self.ai.race.name not in self._user_placements:
            return

        def normalize_map_name(_map_name: str) -> str:
            _map_name = _map_name.lower()
            # List of suffixes to remove
            suffixes = ["le", "aie"]

            # Check for suffixes at the end, with or without a preceding space
            for suffix in suffixes:
                if _map_name.endswith(suffix):
                    _map_name = _map_name[: -len(suffix)]
                elif map_name.endswith(f" {suffix}"):
                    _map_name = _map_name[: -len(suffix) - 1]

            # Remove all spaces and lowercase the name for consistent matching
            return _map_name.replace(" ", "")

        for map_name, placements in self._user_placements[self.ai.race.name].items():
            building_location_info: Optional[dict] = None

            if normalize_map_name(map_name) == normalize_map_name(
                self.ai.game_info.map_name
            ):
                for building_type in placements:
                    if building_type == BuildingPlacementOptions.VS_ZERG_NAT_WALL:
                        if (
                            BuildingPlacementOptions.AVAILABLE_VS_RACES
                            in placements[building_type]
                        ):
                            races: set[str] = {
                                race
                                for race in placements[building_type][
                                    BuildingPlacementOptions.AVAILABLE_VS_RACES
                                ]
                            }

                            if not any(
                                [race in self.ai.enemy_race.name for race in races]
                            ):
                                continue

                        upper_spawn: bool = (
                            self.ai.start_location.y
                            > self.ai.enemy_start_locations[0].y
                        )

                        if (
                            upper_spawn
                            and BuildingPlacementOptions.UPPER_SPAWN
                            in placements[building_type]
                        ):
                            building_location_info = placements[building_type][
                                BuildingPlacementOptions.UPPER_SPAWN
                            ]
                        elif (
                            not upper_spawn
                            and BuildingPlacementOptions.LOWER_SPAWN
                            in placements[building_type]
                        ):
                            building_location_info = placements[building_type][
                                BuildingPlacementOptions.LOWER_SPAWN
                            ]

            if not building_location_info:
                continue

            el: Point2 = self.manager_mediator.get_own_nat
            self.placements_dict[el] = {}
            self.placements_dict[el][BuildingSize.TWO_BY_TWO] = {}
            self.placements_dict[el][BuildingSize.THREE_BY_THREE] = {}

            def log_warning(pos: Point2) -> None:
                logger.warning(
                    f"User passed building location {pos} into "
                    f"`building_locations.yml` but not possible to place it. "
                    f"This building location will be ignored."
                )

            first_pylon: Optional[Point2] = None
            for building, positions in building_location_info.items():
                match building:
                    case BuildingPlacementOptions.FIRST_PYLON:
                        for p in positions:
                            first_pylon = Point2(p)
                            if not self.can_place_structure(first_pylon, UnitID.PYLON):
                                log_warning(first_pylon)
                            else:
                                self._add_placement_position(
                                    BuildingSize.TWO_BY_TWO,
                                    el,
                                    Point2(p),
                                    wall=True,
                                    first_pylon=True,
                                    add_to_avoid_grid=True,
                                )
                    case BuildingPlacementOptions.PYLONS:
                        for p in positions:
                            pos: Point2 = Point2(p)
                            if not self.can_place_structure(pos, UnitID.PYLON):
                                log_warning(pos)
                            else:
                                self._add_placement_position(
                                    BuildingSize.TWO_BY_TWO,
                                    el,
                                    pos,
                                    wall=True,
                                    add_to_avoid_grid=True,
                                    production_pylon=True,
                                )
                    case BuildingPlacementOptions.THREE_BY_THREES:
                        for p in positions:
                            pos: Point2 = Point2(p)
                            if not self.can_place_structure(pos, UnitID.GATEWAY):
                                log_warning(pos)
                            else:
                                self._add_placement_position(
                                    BuildingSize.THREE_BY_THREE,
                                    el,
                                    Point2(p),
                                    wall=True,
                                    add_to_avoid_grid=True,
                                )
                    case BuildingPlacementOptions.STATIC_DEFENCES:
                        for p in positions:
                            pos: Point2 = Point2(p)
                            if not self.can_place_structure(pos, UnitID.SHIELDBATTERY):
                                log_warning(pos)
                            else:
                                self._add_placement_position(
                                    BuildingSize.TWO_BY_TWO,
                                    el,
                                    Point2(p),
                                    static_defence=True,
                                    add_to_avoid_grid=True,
                                )
                    case BuildingPlacementOptions.GATE_KEEPER:
                        for p in positions:
                            self._pvz_nat_gatekeeper_pos = Point2(p)

                if first_pylon:
                    pos_x = int(first_pylon[0] - 8.0)
                    pos_y = int(first_pylon[1] - 8.0)

                    self.points_to_avoid_grid[
                        pos_y : pos_y + 16,
                        pos_x : pos_x + 16,
                    ] = 1

    def _find_potential_placements_at_base(
        self,
        building_size: BuildingSize,
        location: Point2,
        structure_type: UnitID,
        within_psionic_matrix: bool,
        pylon_build_progress: float = 1.0,
    ) -> list[Point2]:
        potential_placements: dict[Point2:dict] = self.placements_dict[location][
            building_size
        ]
        available: list[Point2] = [
            placement
            for placement in potential_placements
            if potential_placements[placement]["available"]
            and not potential_placements[placement]["worker_on_route"]
            and self.can_place_structure(placement, structure_type)
        ]
        if within_psionic_matrix:
            pylons = self.manager_mediator.get_own_structures_dict[UnitID.PYLON]
            available = [
                a
                for a in available
                if cy_pylon_matrix_covers(
                    a,
                    pylons,
                    self.ai.game_info.terrain_height.data_numpy,
                    pylon_build_progress=pylon_build_progress,
                )
            ]

        return available

    def _find_placement_near_pylon(
        self,
        available: list[Point2],
        base_location: Point2,
        pylon_build_progress: float,
        closest_to: Point2,
    ) -> Optional[Point2]:
        pylons = self.manager_mediator.get_own_structures_dict[UnitID.PYLON]
        # first we check for ready pylons
        if available := [
            a
            for a in available
            if cy_pylon_matrix_covers(
                a,
                pylons,
                self.ai.game_info.terrain_height.data_numpy,
                pylon_build_progress=pylon_build_progress,
            )
        ]:
            return min(available, key=lambda k: cy_distance_to_squared(k, closest_to))
        # then check for those in progress
        else:
            if available := [
                a
                for a in available
                if cy_pylon_matrix_covers(
                    a,
                    pylons,
                    self.ai.game_info.terrain_height.data_numpy,
                    pylon_build_progress=pylon_build_progress,
                )
            ]:
                return min(
                    available, key=lambda k: cy_distance_to_squared(k, base_location)
                )

    def on_building_started(self, unit: Unit) -> None:
        """On structure starting, update placements_dict with this new information.

        Parameters
        ----------
        unit :
            A structure that just started building.
        """
        pos: Point2 = unit.position
        for el in self.placements_dict:
            for location in self.placements_dict[el][BuildingSize.TWO_BY_TWO]:
                if location == pos:
                    self._make_placement_unavailable(
                        BuildingSize.TWO_BY_TWO, el, location, unit.tag
                    )
                    return
            for location in self.placements_dict[el][BuildingSize.THREE_BY_THREE]:
                if location == pos:
                    self._make_placement_unavailable(
                        BuildingSize.THREE_BY_THREE, el, location, unit.tag
                    )
                    return

        if pos in self.worker_on_route_tracker:
            self.worker_on_route_tracker.pop(pos)

    def on_building_destroyed(self, unit_tag: int) -> None:
        """On structure destroyed, update placements_dict with this new information.

        Parameters
        ----------
        unit_tag :
            A unit_tag that recently died.
        """

        # quick check to make sure we know about this unit
        # saves running extra logic if not
        if unit_tag not in self.structure_tag_to_base_location:
            return

        # we know about this dead unit, so clean up our records
        base_position: Point2 = self.structure_tag_to_base_location[unit_tag]
        base_structures: dict = self.placements_dict[base_position]
        two_by_two: BuildingSize = BuildingSize.TWO_BY_TWO
        three_by_three: BuildingSize = BuildingSize.THREE_BY_THREE

        for location in base_structures[two_by_two]:
            if unit_tag == base_structures[two_by_two][location]["building_tag"]:
                self._make_placement_available(
                    two_by_two, base_position, location, unit_tag
                )
                return
        for location in base_structures[three_by_three]:
            if unit_tag == base_structures[three_by_three][location]["building_tag"]:
                self._make_placement_available(
                    three_by_three, base_position, location, unit_tag
                )
                return

    def _make_placement_available(
        self,
        size: BuildingSize,
        base_location: Point2,
        building_pos: Point2,
        tag: int = 0,
    ) -> None:
        """Allow a placement to be available again.

        PlacementManager

        Parameters
        ----------
        size :
            The building size.
        base_location :
            Expansion location this placement is near.
        building_pos :
            Unique building placement.
        tag : optional
            Tag of existing structure.
        """
        assert (
            base_location in self.placements_dict
        ), f"{base_location} not in placements dict"
        self.placements_dict[base_location][size][building_pos]["available"] = True
        self.placements_dict[base_location][size][building_pos]["building_tag"] = 0
        self.placements_dict[base_location][size][building_pos][
            "worker_on_route"
        ] = False
        if tag in self.structure_tag_to_base_location:
            self.structure_tag_to_base_location.pop(tag)

    def _make_placement_unavailable(
        self, size: BuildingSize, base_location: Point2, building_pos: Point2, tag: int
    ) -> None:
        """Opposite of `_make_placement_available`.

        PlacementManager

        Parameters
        ----------
        size :
            The building size.
        base_location :
            Expansion location this placement is near.
        building_pos :
            Unique building placement.
        tag :
            Tag of new structure at placement.
        """
        assert (
            base_location in self.placements_dict
        ), f"{base_location} not in placements dict"
        placement_dict: dict = self.placements_dict[base_location][size][building_pos]
        placement_dict["available"] = False
        placement_dict["building_tag"] = tag
        placement_dict["worker_on_route"] = False
        self.structure_tag_to_base_location[tag] = base_location
        if building_pos in self.worker_on_route_tracker:
            self.worker_on_route_tracker.pop(building_pos)

    def _find_placements_for_base_location(
        self,
        el: Point2,
        max_dist: int,
        x_stride: int,
        y_stride: int,
        building_height: int,
        building_width: int,
        building_size: BuildingSize,
        kernel_shape: tuple[int, int],
        reduce_x_stride: bool = False,
        drop_placement_interval: int = 0,
        production_pylon: bool = False,
    ) -> None:
        """
        Find placements at base location using flood fill and convolution
        Parameters
        ----------
        el

        Returns
        -------

        """
        area_points: set[tuple[int, int]] = self.manager_mediator.get_flood_fill_area(
            start_point=el, max_dist=max_dist
        )
        if reduce_x_stride and x_stride >= 7 and len(area_points) < 300:
            x_stride = 5

        raw_x_bounds, raw_y_bounds = cy_get_bounding_box(area_points)

        positions = cy_find_building_locations(
            kernel=np.ones(kernel_shape, dtype=np.uint8),
            x_stride=x_stride,
            y_stride=y_stride,
            x_bounds=raw_x_bounds,
            y_bounds=raw_y_bounds,
            creep_grid=self.creep_grid,
            placement_grid=self.placement_grid,
            pathing_grid=self.pathing_grid,
            points_to_avoid_grid=self.points_to_avoid_grid,
            building_width=building_width,
            building_height=building_height,
            avoid_creep=True,
        )

        for i, pos in enumerate(positions):
            x: float = pos[0]
            y: float = pos[1]
            point2_pos: Point2 = Point2((x, y))
            # drop some placements to avoid walling in
            if (
                drop_placement_interval
                and len(positions) > 6
                and i % drop_placement_interval == 0
            ):
                continue
            if (
                self.ai.get_terrain_height(point2_pos) == self.ai.get_terrain_height(el)
                and cy_distance_to_squared(
                    point2_pos, self.ai.main_base_ramp.top_center
                )
                > 49.0
            ):
                self._add_placement_position(
                    building_size, el, point2_pos, production_pylon=production_pylon
                )
                # move back to top left corner of 3x3, so we can add to avoid grid
                avoid_x = int(x - (building_width / 2))
                avoid_y = int(y - (building_height / 2))
                self.points_to_avoid_grid[
                    avoid_y : avoid_y + kernel_shape[1],
                    avoid_x : avoid_x + kernel_shape[0],
                ] = 1

    def _solve_terran_building_formation(self):
        """Solve Terran building placements for every expansion location.

        The following pseudo logic is applied:
        for every expansion location:
            - get_area_points_near_location (flood fill)
            - use a convolution pass to find 5x3 placements
                this is for rax, factory, starport and addons
            - run another convolution pass to find 2x2 placements
                this is for depots
                avoids found 5x3 placements
            - add found locations to `self.placements_dict`
        """
        self._solve_natural_bunker()
        for el in self.ai.expansion_locations_list:
            if el not in self.placements_dict:
                self.placements_dict[el] = {}
            if BuildingSize.TWO_BY_TWO not in self.placements_dict[el]:
                self.placements_dict[el][BuildingSize.TWO_BY_TWO] = {}
            if BuildingSize.THREE_BY_THREE not in self.placements_dict[el]:
                self.placements_dict[el][BuildingSize.THREE_BY_THREE] = {}

            # avoid building 3x3 within 9 distance of el
            start_x: int = int(el.x - 4.5)
            start_y: int = int(el.y - 4.5)
            self.points_to_avoid_grid[start_y : start_y + 9, start_x : start_x + 9] = 1
            max_dist: int = 16

            # calculate the wall positions first
            if el == self.ai.start_location:
                max_dist = 22
                self._calculate_terran_main_ramp_placements(el)

            x_stride: int = (
                7
                if el == self.ai.start_location
                or el == self.ai.enemy_start_locations[0]
                else 5
            )
            self._find_placements_for_base_location(
                el=el,
                max_dist=max_dist,
                x_stride=x_stride,
                y_stride=3,
                building_height=3,
                building_width=3,
                building_size=BuildingSize.THREE_BY_THREE,
                kernel_shape=(5, 3),
                reduce_x_stride=True,
            )

            # now avoid within 7.5 distance of base location
            start_x = int(el.x - 7.5)
            start_y = int(el.y - 7.5)
            self.points_to_avoid_grid[
                start_y : start_y + 15, start_x : start_x + 15
            ] = 1

            self._find_placements_for_base_location(
                el=el,
                max_dist=max_dist,
                x_stride=2,
                y_stride=2,
                building_height=2,
                building_width=2,
                building_size=BuildingSize.TWO_BY_TWO,
                kernel_shape=(2, 2),
            )

    def _solve_protoss_building_formation(self):
        """Solve Protoss building placements for every expansion location.

        The following pseudo logic is applied:
        for every expansion location:
            - get_area_points_near_location (flood fill)
            - use a convolution pass to find 2x2 production pylons
                set a high x and y stride to space these out
            - run a convolution pass to find 3x3 placements
                this is for gateway, robo, stargate, forge etc
            - run a convolution pass to squeeze in extra 2x2 placements
                this is for supply pylons, cannons, shield batteries
            - add found locations to `self.placements_dict`
        """
        for el in self.ai.expansion_locations_list:
            if el not in self.placements_dict:
                self.placements_dict[el] = {}
                self.placements_dict[el][BuildingSize.TWO_BY_TWO] = {}
                self.placements_dict[el][BuildingSize.THREE_BY_THREE] = {}
            # avoid building within 9 distance of el
            start_x: int = int(el.x - 5)
            start_y: int = int(el.y - 5)
            self.points_to_avoid_grid[
                start_y : start_y + 10, start_x : start_x + 10
            ] = 1
            max_dist: int = 16
            # calculate the wall positions first
            if el == self.ai.start_location:
                max_dist = 22
                self._calculate_protoss_main_ramp_placements(el)

            # find prod pylons first
            self._find_placements_for_base_location(
                el=el,
                max_dist=max_dist,
                x_stride=7,
                y_stride=7,
                building_height=2,
                building_width=2,
                building_size=BuildingSize.TWO_BY_TWO,
                kernel_shape=(2, 2),
                production_pylon=True,
            )

            # fit in 3x3 after
            self._find_placements_for_base_location(
                el=el,
                max_dist=max_dist,
                x_stride=3,
                y_stride=3,
                building_height=3,
                building_width=3,
                building_size=BuildingSize.THREE_BY_THREE,
                kernel_shape=(3, 3),
            )

            # find extra 2x2 last
            self._find_placements_for_base_location(
                el=el,
                max_dist=max_dist,
                x_stride=2,
                y_stride=3,
                building_height=2,
                building_width=2,
                building_size=BuildingSize.TWO_BY_TWO,
                kernel_shape=(2, 2),
            )

            # find optimal pylon to build around (fits most 3x3)
            self._find_optimal_pylon_for_base(el)

    def _find_optimal_pylon_for_base(self, el: Point2) -> None:
        two_by_twos: dict[Point2:dict] = self.placements_dict[el][
            BuildingSize.TWO_BY_TWO
        ]
        prod_pylons: list[Point2] = [
            placement
            for placement in two_by_twos
            if two_by_twos[placement]["production_pylon"]
        ]
        three_by_threes: dict[Point2:dict] = self.placements_dict[el][
            BuildingSize.THREE_BY_THREE
        ]

        if not prod_pylons or not three_by_threes:
            return

        best_pylon_pos: Point2 = prod_pylons[0]
        most_three_by_threes: int = 0

        for pylon_position in prod_pylons:
            num_three_by_threes: int = 0
            for three_by_three in three_by_threes:
                if cy_distance_to_squared(pylon_position, three_by_three) < 42.25:
                    num_three_by_threes += 1
            if num_three_by_threes >= most_three_by_threes:
                most_three_by_threes = num_three_by_threes
                best_pylon_pos = pylon_position

        try:
            self.placements_dict[el][BuildingSize.TWO_BY_TWO][best_pylon_pos][
                "optimal_pylon"
            ] = True
        except KeyError:
            logger.warning(
                f"Could not set optimal pylon for base {el}, "
                f"position {best_pylon_pos} not found"
            )

    def _solve_zerg_building_formation(self):
        # TODO: Implement zerg placements
        pass

    def _add_placement_position(
        self,
        building_size: BuildingSize,
        expansion_location: Point2,
        position: Point2,
        production_pylon: bool = False,
        wall: bool = False,
        bunker: bool = False,
        optimal_pylon: bool = False,
        first_pylon: bool = False,
        static_defence: bool = False,
        add_to_avoid_grid: bool = False,
    ) -> None:
        """Add calculated position to placements dict."""
        self.placements_dict[expansion_location][building_size][position] = {
            "available": True,
            "has_addon": False,
            "is_wall": wall,
            "building_tag": 0,
            "worker_on_route": False,
            "time_requested": 0.0,
            "production_pylon": production_pylon,
            "bunker": bunker,
            "optimal_pylon": optimal_pylon,
            "first_pylon": first_pylon,
            "static_defence": static_defence,
        }
        if add_to_avoid_grid:
            if building_size == BuildingSize.TWO_BY_TWO:
                building_x = int(position.x - 1.0)
                building_y = int(position.y - 1.0)

                self.points_to_avoid_grid[
                    building_y : building_y + 2,
                    building_x : building_x + 2,
                ] = 1
            elif building_size == BuildingSize.THREE_BY_THREE:
                building_x = int(position.x - 1.5)
                building_y = int(position.y - 1.5)

                self.points_to_avoid_grid[
                    building_y : building_y + 3,
                    building_x : building_x + 3,
                ] = 1

    def _calculate_protoss_main_ramp_placements(self, el: Point2) -> Point2:
        """

        Parameters
        ----------
        el

        Returns
        -------
        The pylon position
        """
        pylon_pos: Point2 = self.ai.main_base_ramp.protoss_wall_pylon
        buildings: FrozenSet[Point2] = self.ai.main_base_ramp.protoss_wall_buildings

        self._add_placement_position(
            BuildingSize.TWO_BY_TWO, el, pylon_pos, wall=True, production_pylon=True
        )
        building_positions = [pos for pos in buildings]
        self._add_placement_position(
            BuildingSize.THREE_BY_THREE, el, building_positions[0], wall=True
        )
        self._add_placement_position(
            BuildingSize.THREE_BY_THREE, el, building_positions[1], wall=True
        )
        ramp_2x2_x = int(pylon_pos.x - 1.0)
        ramp_2x2_y = int(pylon_pos.y - 1.0)

        building_wall_1_x = int(building_positions[0].x - 1.5)
        building_wall_1_y = int(building_positions[0].y - 1.5)
        building_wall_2_x = int(building_positions[1].x - 1.5)
        building_wall_2_y = int(building_positions[1].y - 1.5)

        self.points_to_avoid_grid[
            ramp_2x2_y : ramp_2x2_y + 2, ramp_2x2_x : ramp_2x2_x + 2
        ] = 1
        self.points_to_avoid_grid[
            building_wall_1_y : building_wall_1_y + 3,
            building_wall_1_x : building_wall_1_x + 3,
        ] = 1
        self.points_to_avoid_grid[
            building_wall_2_y : building_wall_2_y + 3,
            building_wall_2_x : building_wall_2_x + 3,
        ] = 1

        return pylon_pos

    def _calculate_terran_main_ramp_placements(self, el: Point2) -> None:
        ramp = self.ai.main_base_ramp
        center_pos: Point2 = ramp.barracks_correct_placement
        self._add_placement_position(
            BuildingSize.THREE_BY_THREE, el, center_pos, wall=True
        )
        corner_positions = [pos for pos in ramp.corner_depots]
        self._add_placement_position(
            BuildingSize.TWO_BY_TWO,
            el,
            corner_positions[0],
            wall=True,
        )
        self._add_placement_position(
            BuildingSize.TWO_BY_TWO,
            el,
            corner_positions[1],
            wall=True,
        )
        ramp_3x3_x = int(ramp.barracks_correct_placement.x - 1.5)
        ramp_3x3_y = int(ramp.barracks_correct_placement.y - 1.5)
        corner_wall_1_x = int(corner_positions[0].x - 1.0)
        corner_wall_1_y = int(corner_positions[0].y - 1.0)
        corner_wall_2_x = int(corner_positions[1].x - 1.0)
        corner_wall_2_y = int(corner_positions[1].y - 1.0)

        self.points_to_avoid_grid[
            ramp_3x3_y : ramp_3x3_y + 3, ramp_3x3_x : ramp_3x3_x + 5
        ] = 1
        self.points_to_avoid_grid[
            corner_wall_1_y : corner_wall_1_y + 2,
            corner_wall_1_x : corner_wall_1_x + 2,
        ] = 1
        self.points_to_avoid_grid[
            corner_wall_2_y : corner_wall_2_y + 2,
            corner_wall_2_x : corner_wall_2_x + 2,
        ] = 1

    async def _draw_building_placements(self):
        """Draw all found building placements.

        Debug and DebugOptions.ShowBuildingFormation should be True in config to enable.
        """

        for location in self.placements_dict:

            three_by_three = self.placements_dict[location][BuildingSize.THREE_BY_THREE]
            two_by_two = self.placements_dict[location][BuildingSize.TWO_BY_TWO]
            z = self.ai.get_terrain_height(location)
            z = -16 + 32 * z / 255

            for placement in three_by_three:
                info = self.placements_dict[location][BuildingSize.THREE_BY_THREE][
                    placement
                ]
                position: Point2 = Point2(placement)
                self.ai.draw_text_on_world(position, f"{placement}")
                pos_min = Point3((placement.x - 1.5, placement.y - 1.5, z))
                pos_max = Point3((placement.x + 1.5, placement.y + 1.5, z + 2))
                if info["bunker"]:
                    colour = Point3((0, 255, 0))
                elif info["is_wall"]:
                    colour = Point3((255, 255, 0))
                else:
                    colour = Point3((0, 0, 255))
                self.ai.client.debug_box_out(pos_min, pos_max, colour)
                if self.ai.race == Race.Terran and not info["bunker"]:
                    pos_min = Point3((placement.x + 1.5, placement.y + 0.5, z))
                    pos_max = Point3((placement.x + 3.5, placement.y - 1.5, z + 1))
                    self.ai.client.debug_box_out(pos_min, pos_max, Point3((0, 0, 255)))

            for placement in two_by_two:
                info = self.placements_dict[location][BuildingSize.TWO_BY_TWO][
                    placement
                ]
                position: Point2 = Point2(placement)
                self.ai.draw_text_on_world(position, f"{placement}")
                pos_min = Point3((placement.x - 1.0, placement.y - 1.0, z))
                pos_max = Point3((placement.x + 1.0, placement.y + 1.0, z + 1))
                if info["first_pylon"]:
                    colour = Point3((255, 255, 255))
                elif info["is_wall"]:
                    colour = Point3((255, 255, 0))
                elif info["static_defence"]:
                    colour = Point3((0, 255, 255))
                elif info["optimal_pylon"]:
                    colour = Point3((255, 0, 0))
                elif info["production_pylon"]:
                    colour = Point3((0, 255, 0))
                else:
                    colour = Point3((0, 0, 255))
                self.ai.client.debug_box_out(pos_min, pos_max, colour)

    def _track_requested_placements(self) -> None:
        """Track requested placements, and check if they should be made available.

        request_building_placement will reserve placements, so they are not selected
        multiple times. This will make those placements available again after a set
        duration.
        """
        loc_to_remove: list[Point2] = []
        two_by_two: BuildingSize = BuildingSize.TWO_BY_TWO
        three_by_three: BuildingSize = BuildingSize.THREE_BY_THREE
        for (
            building_location,
            base_location,
        ) in self.worker_on_route_tracker.items():
            base_placements: dict = self.placements_dict[base_location]
            if building_location in base_placements[two_by_two]:
                if (
                    self.ai.time
                    > base_placements[two_by_two][building_location]["time_requested"]
                    + self.WORKER_ON_ROUTE_TIMEOUT
                ):
                    self._make_placement_available(
                        two_by_two, base_location, building_location
                    )
                    loc_to_remove.append(building_location)

            elif building_location in base_placements[three_by_three]:
                if (
                    self.ai.time
                    > base_placements[three_by_three][building_location][
                        "time_requested"
                    ]
                    + self.WORKER_ON_ROUTE_TIMEOUT
                ):
                    self._make_placement_available(
                        three_by_three, base_location, building_location
                    )
                    loc_to_remove.append(building_location)

        for loc in loc_to_remove:
            self.worker_on_route_tracker.pop(loc)

    def _solve_natural_bunker(self):
        nat_location: Point2 = self.manager_mediator.get_own_nat
        start_x: int = int(nat_location.x - 4.5)
        start_y: int = int(nat_location.y - 4.5)
        self.points_to_avoid_grid[start_y : start_y + 9, start_x : start_x + 9] = 1
        self.placements_dict[nat_location] = {}
        self.placements_dict[nat_location][BuildingSize.THREE_BY_THREE] = {}

        size: BuildingSize = STRUCTURE_TO_BUILDING_SIZE[UnitID.BUNKER]

        towards_ramp: tuple[float, float] = cy_towards(
            nat_location, self.ai.main_base_ramp.bottom_center, 4.0
        )
        towards_center: tuple[float, float] = cy_towards(
            towards_ramp, self.ai.game_info.map_center, 6.0
        )
        goal_x: int = int(towards_center[0])
        goal_y: int = int(towards_center[1])

        for x, y in product(range(-2, 2), range(-2, 2)):
            pos: Point2 = Point2((goal_x + x, goal_y + y))
            if self.can_place_structure(pos, UnitID.BUNKER):
                self._add_placement_position(size, nat_location, pos, bunker=True)
                avoid_x = int(pos.x - 1.5)
                avoid_y = int(pos.y - 1.5)
                self.points_to_avoid_grid[
                    avoid_y : avoid_y + 3, avoid_x : avoid_x + 3
                ] = 1
                break
