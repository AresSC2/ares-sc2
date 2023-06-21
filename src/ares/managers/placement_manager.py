import time
from typing import TYPE_CHECKING, Any, Callable, Coroutine, DefaultDict, Optional, Union

import numpy as np
from loguru import logger
from sc2.data import Race
from sc2.position import Point2, Point3
from sc2.unit import Unit

from ares.consts import (
    DEBUG,
    DEBUG_OPTIONS,
    PLACEMENT,
    SHOW_BUILDING_FORMATION,
    WORKER_ON_ROUTE_TIMEOUT,
    BuildingSize,
    ManagerName,
    ManagerRequestType,
)
from ares.cython_extensions.cython_functions import get_bounding_box
from ares.cython_extensions.placement_solver import (
    can_place_structure,
    find_building_locations,
)
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
            ManagerRequestType.REQUEST_BUILDING_PLACEMENT: lambda kwargs: (
                self.request_building_placement(**kwargs)
            ),
        }

        # main dict where all data is organised
        # {base_loc: 3x3: {building_pos: (2, 2), taken: False, is_wall: True}, {...}
        #            2x2: {building_pos: (5, 5), taken: True, is_wall: False}, {...}}
        self.placements_dict: dict[Point2 : dict[BuildingSize:dict]] = dict()
        self.race_to_building_solver_method: dict[Race:Callable] = {
            Race.Terran: lambda: self._solve_terran_building_formation(),
            Race.Protoss: lambda: self._solve_protoss_building_formation(),
            Race.Zerg: lambda: self._solve_zerg_building_formation(),
        }
        # this is to allow faster lookup of placements_dict
        self.structure_tag_to_base_location: dict[int, Point2] = dict()
        # this prevents iterating through all bases to check workers on route
        # key: Unique placement location, value: main base location
        self.worker_on_route_tracker: dict[Point2:Point2] = dict()
        self.WORKER_ON_ROUTE_TIMEOUT: float = self.config[PLACEMENT][
            WORKER_ON_ROUTE_TIMEOUT
        ]

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
        # occasionally check if worker on route locations can be unlocked
        if iteration % 16 == 0 and len(self.worker_on_route_tracker) > 0:
            self._track_requested_placements()

        if self.config[DEBUG] and self.config[DEBUG_OPTIONS][SHOW_BUILDING_FORMATION]:
            await self._draw_building_placements()

    async def initialise(self) -> None:
        """Calculate building formations on game commencement."""
        self.points_to_avoid_grid = np.zeros(
            self.ai.game_info.placement_grid.data_numpy.shape, dtype=np.uint8
        )
        start: float = time.time()
        self.race_to_building_solver_method[self.ai.race]()
        finish: float = time.time()
        logger.info(f"Solved placement formation in {(finish - start)*1000} ms")

    def can_place_structure(
        self, position: Point2, size: BuildingSize, include_addon: bool = False
    ) -> bool:
        """Check if structure can be placed at a given position.

        Faster cython alternative to `python-sc2` `await self.can_place()`

        Parameters
        ----------
        position : Point2
            The intended building position.
        size : BuildingSize
            Size of intended structure.
        include_addon : bool, optional
            For Terran structures, check addon will place too.

        Returns
        ----------
        bool :
            Indicating if structure can be placed at given position.
        """
        offset: float = self.BUILDING_SIZE_ENUM_TO_RADIUS[size]
        origin_x: int = int(position[0] - offset)
        origin_y: int = int(position[1] - offset)

        size: tuple[int, int] = self.BUILDING_SIZE_ENUM_TO_TUPLE[size]
        return can_place_structure(
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
        building_size: BuildingSize,
        wall: bool = False,
        find_alternative: bool = True,
        reserve_placement: bool = True,
    ) -> Optional[Point2]:
        """Given a base location and building size find an available placement.
        TODO: Implement find_alternative parameter where method will find a nearby
            placement if none available at `base_location`

        Parameters
        ----------
        base_location : Point2
            The general area where the placement should be near.
            This should be a expansion location.
        building_size : BuildingSize
            Size of intended structure.
        wall : bool, optional
            Request a wall structure placement.
            Will find alternative if no wall placements available.
        find_alternative : bool, optional (NOT YET IMPLEMENTED)
            If no placements available at base_location, find
            alternative at nearby base.
        reserve_placement : bool, optional
            Reserve this booking for a while, so another customer doesnt
            request it.

        Returns
        ----------
        bool :
            Indicating if structure can be placed at given position.

        """
        assert (
            self.ai.race == Race.Terran
        ), "`request_building_placement` only currently supported for Terran"

        # find base location in placements_dict, or find closest
        location: Point2 = (
            base_location
            if base_location in self.placements_dict
            else min(
                self.placements_dict.keys(),
                key=lambda k: k.distance_to(base_location),
            )
        )

        if building_size in self.placements_dict[location]:
            potential_placements: dict[Point2:dict] = self.placements_dict[location][
                building_size
            ]
            # find all available building_size placements at this base location
            available: list[Point2] = [
                placement
                for placement in potential_placements
                if potential_placements[placement]["available"]
                and not potential_placements[placement]["worker_on_route"]
                and self.can_place_structure(placement, building_size)
            ]
            if len(available) == 0:
                logger.warning(
                    f"No available {building_size} found near location: {base_location}"
                )
                return

            # get closest available by default
            final_placement: Point2 = min(
                available, key=lambda k: k.distance_to(base_location)
            )
            # if wall placement is requested swap final_placement is possible
            if wall:
                if available := [
                    a
                    for a in available
                    if self.placements_dict[location][building_size][a]["is_wall"]
                ]:
                    final_placement = min(
                        available, key=lambda k: k.distance_to(base_location)
                    )

            if reserve_placement:
                self.worker_on_route_tracker[final_placement] = location
                potential_placements[final_placement]["worker_on_route"] = True
                potential_placements[final_placement]["time_requested"] = self.ai.time

            return final_placement

        else:
            logger.warning(f"No {building_size} present in placement bookkeeping.")

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
        creep_grid: np.ndarray = self.ai.state.creep.data_numpy
        placement_grid: np.ndarray = self.ai.game_info.placement_grid.data_numpy
        # Note: use MapAnalyzers pathing grid to get rocks etc
        pathing_grid: np.ndarray = self.manager_mediator.get_ground_grid.astype(
            np.uint8
        ).T
        for el in self.ai.expansion_locations_list:
            self.placements_dict[el] = {}
            self.placements_dict[el][BuildingSize.TWO_BY_TWO] = {}
            self.placements_dict[el][BuildingSize.THREE_BY_THREE] = {}
            # avoid building 3x3 within 9 distance of el
            start_x: int = int(el.x - 4.5)
            start_y: int = int(el.y - 4.5)
            self.points_to_avoid_grid[start_y : start_y + 9, start_x : start_x + 9] = 1
            max_dist: int = 16

            # calculate the wall positions first
            if el == self.ai.start_location:
                max_dist = 22
                ramp = self.ai.main_base_ramp
                self.placements_dict[el][BuildingSize.THREE_BY_THREE][
                    ramp.barracks_correct_placement
                ] = {
                    "available": True,
                    "has_addon": False,
                    "is_wall": True,
                    "building_tag": 0,
                    "worker_on_route": False,
                    "time_requested": 0.0,
                }
                depot_positions = [pos for pos in ramp.corner_depots]
                self.placements_dict[el][BuildingSize.TWO_BY_TWO][
                    depot_positions[0]
                ] = {
                    "available": True,
                    "has_addon": False,
                    "is_wall": True,
                    "building_tag": 0,
                    "worker_on_route": False,
                    "time_requested": 0.0,
                }
                self.placements_dict[el][BuildingSize.TWO_BY_TWO][
                    depot_positions[1]
                ] = {
                    "available": True,
                    "has_addon": False,
                    "is_wall": True,
                    "building_tag": 0,
                    "worker_on_route": False,
                    "time_requested": 0.0,
                }
                ramp_rax_x = int(ramp.barracks_correct_placement.x - 1.5)
                ramp_rax_y = int(ramp.barracks_correct_placement.y - 1.5)
                depot_wall_1_x = int(depot_positions[0].x - 1.0)
                depot_wall_1_y = int(depot_positions[0].y - 1.0)
                depot_wall_2_x = int(depot_positions[1].x - 1.0)
                depot_wall_2_y = int(depot_positions[1].y - 1.0)

                self.points_to_avoid_grid[
                    ramp_rax_y : ramp_rax_y + 3, ramp_rax_x : ramp_rax_x + 5
                ] = 1
                self.points_to_avoid_grid[
                    depot_wall_1_y : depot_wall_1_y + 2,
                    depot_wall_1_x : depot_wall_1_x + 2,
                ] = 1
                self.points_to_avoid_grid[
                    depot_wall_2_y : depot_wall_2_y + 2,
                    depot_wall_2_x : depot_wall_2_x + 2,
                ] = 1

            area_points: set[
                tuple[int, int]
            ] = self.manager_mediator.get_flood_fill_area(
                start_point=el, max_dist=max_dist
            )
            raw_x_bounds, raw_y_bounds = get_bounding_box(area_points)

            three_by_three_positions = find_building_locations(
                kernel=np.ones((5, 3), dtype=np.uint8),
                x_stride=5,
                y_stride=3,
                x_bounds=raw_x_bounds,
                y_bounds=raw_y_bounds,
                creep_grid=creep_grid,
                placement_grid=placement_grid,
                pathing_grid=pathing_grid,
                points_to_avoid_grid=self.points_to_avoid_grid,
                building_width=3,
                building_height=3,
                avoid_creep=True,
            )

            for pos in three_by_three_positions:
                x: float = pos[0]
                y: float = pos[1]
                point2_pos: Point2 = Point2((x, y))
                if self.ai.get_terrain_height(point2_pos) == self.ai.get_terrain_height(
                    el
                ):
                    self.placements_dict[el][BuildingSize.THREE_BY_THREE][
                        point2_pos
                    ] = {
                        "available": True,
                        "has_addon": False,
                        "is_wall": False,
                        "building_tag": 0,
                        "worker_on_route": False,
                        "time_requested": 0.0,
                    }
                    # move back to top left corner of 3x3, so we can add to avoid grid
                    avoid_x = int(x - 1.5)
                    avoid_y = int(y - 1.5)
                    self.points_to_avoid_grid[
                        avoid_y : avoid_y + 3, avoid_x : avoid_x + 5
                    ] = 1

            # avoid within 7.5 distance of base location
            start_x = int(el.x - 7.5)
            start_y = int(el.y - 7.5)
            self.points_to_avoid_grid[
                start_y : start_y + 15, start_x : start_x + 15
            ] = 1
            supply_positions = find_building_locations(
                kernel=np.ones((2, 2), dtype=np.uint8),
                x_stride=2,
                y_stride=2,
                x_bounds=raw_x_bounds,
                y_bounds=raw_y_bounds,
                creep_grid=creep_grid,
                placement_grid=placement_grid,
                pathing_grid=pathing_grid,
                points_to_avoid_grid=self.points_to_avoid_grid,
                building_width=2,
                building_height=2,
                avoid_creep=True,
            )

            for pos in supply_positions:
                x: float = pos[0]
                y: float = pos[1]
                point2_pos: Point2 = Point2((x, y))
                if self.ai.get_terrain_height(point2_pos) == self.ai.get_terrain_height(
                    el
                ):
                    self.placements_dict[el][BuildingSize.TWO_BY_TWO][point2_pos] = {
                        "available": True,
                        "has_addon": False,
                        "is_wall": False,
                        "building_tag": 0,
                        "worker_on_route": False,
                        "time_requested": 0.0,
                    }
                    # move back to top left corner of 2x2, so we can add to avoid grid
                    avoid_x = int(x - 1.0)
                    avoid_y = int(y - 1.0)
                    self.points_to_avoid_grid[
                        avoid_y : avoid_y + 2, avoid_x : avoid_x + 2
                    ] = 1

    def _solve_protoss_building_formation(self):
        # TODO: Implement protoss placements
        pass

    def _solve_zerg_building_formation(self):
        # TODO: Implement zerg placements
        pass

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
                self.ai.draw_text_on_world(Point2(placement), f"{placement}")
                pos_min = Point3((placement.x - 1.5, placement.y - 1.5, z))
                pos_max = Point3((placement.x + 1.5, placement.y + 1.5, z + 2))
                self.ai.client.debug_box_out(pos_min, pos_max, Point3((255, 0, 0)))
                if self.ai.race == Race.Terran:
                    pos_min = Point3((placement.x + 1.5, placement.y + 0.5, z))
                    pos_max = Point3((placement.x + 3.5, placement.y - 1.5, z + 1))
                    self.ai.client.debug_box_out(pos_min, pos_max, Point3((0, 255, 0)))

            for placement in two_by_two:
                pos_min = Point3((placement.x - 1.0, placement.y - 1.0, z))
                pos_max = Point3((placement.x + 1.0, placement.y + 1.0, z + 1))
                self.ai.client.debug_box_out(pos_min, pos_max, Point3((0, 0, 255)))

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
                    base_placements[two_by_two][building_location]["available"] = True
                    loc_to_remove.append(building_location)

            elif building_location in base_placements[three_by_three]:
                if (
                    self.ai.time
                    > base_placements[three_by_three][building_location][
                        "time_requested"
                    ]
                    + self.WORKER_ON_ROUTE_TIMEOUT
                ):
                    base_placements[three_by_three][building_location][
                        "available"
                    ] = True
                    loc_to_remove.append(building_location)

        for loc in loc_to_remove:
            self.worker_on_route_tracker.pop(loc)
