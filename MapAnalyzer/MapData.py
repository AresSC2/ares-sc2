import math
import time
from itertools import chain
from functools import lru_cache
from os import mkdir, path
from typing import Dict, List, Optional, Set, Tuple, Union

import numpy as np
from loguru import logger
from numpy import float64, ndarray
from pkg_resources import DistributionNotFound, get_distribution
from sc2.bot_ai import BotAI
from sc2.position import Point2
from scipy.ndimage import (
    binary_fill_holes,
    center_of_mass,
    generate_binary_structure,
    label as ndlabel,
)
from scipy.spatial import distance

from MapAnalyzer.Debugger import MapAnalyzerDebugger
from MapAnalyzer.Pather import MapAnalyzerPather
from MapAnalyzer.Region import Region
from MapAnalyzer.utils import get_sets_with_mutual_elements, fix_map_ramps

from .constants import (
    BINARY_STRUCTURE,
    CORNER_MIN_DISTANCE,
    MAX_REGION_AREA,
    MIN_REGION_AREA,
)

from .decorators import progress_wrapped
from .exceptions import CustomDeprecationWarning
from MapAnalyzer.constructs import ChokeArea, MDRamp, VisionBlockerArea, RawChoke
from .cext import CMapInfo, CMapChoke

try:
    __version__ = get_distribution("sc2mapanalyzer")
except DistributionNotFound:
    __version__ = "dev"

WHITE = "\u001b[32m"


class MapData:
    """

    Entry point for the user

    """

    def __init__(
        self,
        bot: BotAI,
        loglevel: str = "ERROR",
        arcade: bool = False,
        corner_distance: int = CORNER_MIN_DISTANCE,
    ) -> None:
        # store relevant data from api
        self.bot = bot
        # temporary fix to set ramps correctly if they are broken in burnysc2 due to having
        # destructables on them. ramp sides don't consider the destructables now,
        # should update them during the game
        (
            self.bot.game_info.map_ramps,
            self.bot.game_info.vision_blockers,
        ) = fix_map_ramps(self.bot)

        self.corner_distance = (
            corner_distance  # the lower this value is,  the sharper the corners will be
        )
        self.arcade = arcade
        self.version = __version__
        self.map_name: str = bot.game_info.map_name
        self.placement_arr: ndarray = bot.game_info.placement_grid.data_numpy
        self.path_arr: ndarray = bot.game_info.pathing_grid.data_numpy
        self.mineral_fields = bot.mineral_field
        self.normal_geysers = bot.vespene_geyser
        self.terrain_height: ndarray = bot.game_info.terrain_height.data_numpy
        self._vision_blockers: Set[Point2] = bot.game_info.vision_blockers

        # data that will be generated and cached
        self.regions: dict = {}  # set later
        self.region_grid: Optional[ndarray] = None
        self.corners: list = []  # set later
        self.polygons: list = []  # set later
        self.map_chokes: list = []  # set later on compile
        self.map_ramps: list = []  # set later on compile
        self.map_vision_blockers: list = []  # set later on compile
        self.vision_blockers_labels: list = []  # set later on compile
        self.vision_blockers_grid: Optional[ndarray] = None  # set later on compile
        self.overlord_spots: list = []
        self.resource_blockers = [
            Point2((m.position[0], m.position[1]))
            for m in self.bot.all_units
            if any(x in m.name.lower() for x in {"rich", "450"})
        ]

        # store extended_arrays in one matrix to save computation on compile (set later)
        self.extended_array_matrix: Optional[np.ndarray] = None

        pathing_grid = np.fmax(self.path_arr, self.placement_arr)
        self.c_ext_map = CMapInfo(
            pathing_grid.T,
            self.terrain_height.T,
            self.bot.game_info.playable_area,
            self.bot.game_info.map_name,
        )
        self.overlord_spots = self.c_ext_map.overlord_spots

        # plugins
        self.log_level = loglevel
        self.debugger = MapAnalyzerDebugger(self, loglevel=self.log_level)
        self.pather = MapAnalyzerPather(self)

        self.connectivity_graph = None  # set by pather

        # compile
        if not self.arcade:
            self.base_locations: list = bot.expansion_locations_list
        else:
            logger.info(f" {__version__} Starting in Arcade mode")
            self.base_locations: list = []

        logger.info(f"{__version__} Compiling {self.map_name} " + WHITE)

        self._compile_map()

    """Properties"""

    @property
    def vision_blockers(self) -> Set[Point2]:
        """
        Exposing the computed method

            ``vision_blockers`` are not to be confused with :data:`self.map_vision_blockers`
            ``vision_blockers`` are the raw data received from ``burnysc2`` and will be processed later on.

        """
        return self._vision_blockers

    """ Pathing methods"""

    # dont cache this
    def get_pyastar_grid(
        self, default_weight: float = 1, include_destructables: bool = True
    ) -> ndarray:
        """
        :rtype: numpy.ndarray
        Note:
            To query what is the cost in a certain point, simple do ``my_grid[certain_point]`` where `certain_point`

            is a :class:`tuple` or a :class:`sc2.position.Point2`


        Requests a new pathing grid.

        This grid will have all non pathable cells set to :class:`numpy.inf`.

        pathable cells will be set to the ``default_weight`` which it's default is ``1``.

        After you get the grid, you can add your own ``cost`` (also known as ``weight`` or ``influence``)

        This grid can, and **should** be reused in the duration of the frame,
        and should be regenerated(**once**) on each frame.

        Note:
            destructables that has been destroyed will be updated by default,

            the only known use case for ``include_destructables`` usage is illustrated in the first example below

        Example:
            We want to check if breaking the destructables in our path will make it better,

            so we treat destructables as if they were pathable

            >>> no_destructables_grid = self.get_pyastar_grid(default_weight = 1, include_destructables= False)
            >>> # 2 set up a grid with default weight of 300
            >>> custom_weight_grid = self.get_pyastar_grid(default_weight = 300)

        See Also:
            * :meth:`.MapData.get_climber_grid`
            * :meth:`.MapData.get_air_vs_ground_grid`
            * :meth:`.MapData.get_clean_air_grid`
            * :meth:`.MapData.add_cost`
            * :meth:`.MapData.pathfind`
            * :meth:`.MapData.find_lowest_cost_points`

        """
        return self.pather.get_pyastar_grid(
            default_weight=default_weight,
            include_destructables=include_destructables,
        )

    def find_lowest_cost_points(
        self, from_pos: Point2, radius: float, grid: np.ndarray
    ) -> List[Point2]:
        """
        :rtype:  Union[List[:class:`sc2.position.Point2`], None]

        Given an origin point and a radius,  will return a list containing the lowest cost points
        (if there are more than one)

        Example:

             >>> my_grid = self.get_air_vs_ground_grid()
             >>> position = (100, 80)
             >>> my_radius = 10
             >>> self.find_lowest_cost_points(from_pos=position, radius=my_radius, grid=my_grid)
             [(90, 80), (91, 76), (91, 77), (91, 78), (91, 79), (91, 80), (91, 81), (92, 74), (92, 75), (92, 76), (92, 77), (92, 78), (92, 79), (92, 80), (92, 81), (93, 73), (93, 74), (93, 75), (93, 76), (93, 77), (93, 78), (93, 79), (93, 80), (93, 81), (94, 72), (94, 73), (94, 74), (94, 75), (94, 76), (94, 77), (95, 73), (95, 74), (95, 75), (95, 76), (96, 74), (96, 75), (97, 74), (97, 75), (98, 74), (98, 75), (99, 74), (99, 75), (100, 74), (100, 75), (101, 74), (101, 75), (102, 74), (102, 75), (103, 74), (103, 75), (104, 74), (104, 75), (105, 74), (105, 75), (106, 74), (106, 75), (107, 74), (107, 75), (108, 74), (108, 75)]

        See Also:
            * :meth:`.MapData.get_pyastar_grid`
            * :meth:`.MapData.get_climber_grid`
            * :meth:`.MapData.get_air_vs_ground_grid`
            * :meth:`.MapData.get_clean_air_grid`
            * :meth:`.MapData.add_cost`
            * :meth:`.MapData.pathfind`

        """
        return self.pather.find_lowest_cost_points(
            from_pos=from_pos, radius=radius, grid=grid
        )

    def lowest_cost_points_array(
        self, from_pos: Point2, radius: float, grid: np.ndarray
    ) -> ndarray:
        """
        :rtype:    Union[:class:`numpy.ndarray`, None]
        Same as find_lowest_cost_points, but returns points in ndarray for use

        with numpy/scipy/etc
        """
        return self.pather.lowest_cost_points_array(
            from_pos=from_pos, radius=radius, grid=grid
        )

    def get_climber_grid(
        self, default_weight: float = 1, include_destructables: bool = True
    ) -> ndarray:
        """
        :rtype: numpy.ndarray
        Climber grid is a grid modified by the c extension, and is used for units that can climb,

        such as Reaper, Colossus

        This grid can be reused in the duration of the frame,

        and should be regenerated(once) on each frame.

        This grid also gets updated with all nonpathables when requested

        such as structures, and destructables

        Example:
                >>> updated_climber_grid = self.get_climber_grid(default_weight = 1)

        See Also:
            * :meth:`.MapData.get_pyastar_grid`
            * :meth:`.MapData.get_air_vs_ground_grid`
            * :meth:`.MapData.get_clean_air_grid`
            * :meth:`.MapData.add_cost`
            * :meth:`.MapData.pathfind`
            * :meth:`.MapData.find_lowest_cost_points`
        """
        return self.pather.get_climber_grid(
            default_weight, include_destructables=include_destructables
        )

    def get_air_vs_ground_grid(self, default_weight: float = 100) -> ndarray:
        """
        :rtype: numpy.ndarray
        ``air_vs_ground`` grid is computed in a way that lowers the cost of nonpathable terrain,

         making air units naturally "drawn" to it.

        Caution:
            Requesting a grid with a ``default_weight`` of 1 is pointless,

            and  will result in a :meth:`.MapData.get_clean_air_grid`

        Example:
                >>> air_vs_ground_grid = self.get_air_vs_ground_grid()

        See Also:
            * :meth:`.MapData.get_pyastar_grid`
            * :meth:`.MapData.get_climber_grid`
            * :meth:`.MapData.get_clean_air_grid`
            * :meth:`.MapData.add_cost`
            * :meth:`.MapData.pathfind`
            * :meth:`.MapData.find_lowest_cost_points`

        """
        return self.pather.get_air_vs_ground_grid(default_weight=default_weight)

    def get_clean_air_grid(self, default_weight: float = 1) -> ndarray:
        """

        :rtype: numpy.ndarray

        Will return a grid marking every cell as pathable with ``default_weight``

        See Also:
            * :meth:`.MapData.get_air_vs_ground_grid`

        """
        return self.pather.get_clean_air_grid(default_weight=default_weight)

    def pathfind(
        self,
        start: Union[Tuple[float, float], Point2],
        goal: Union[Tuple[float, float], Point2],
        grid: Optional[ndarray] = None,
        large: bool = False,
        smoothing: bool = False,
        sensitivity: int = 1,
    ) -> Optional[List[Point2]]:
        """
        :rtype: Union[List[:class:`sc2.position.Point2`], None]
        Will return the path with lowest cost (sum) given a weighted array (``grid``), ``start`` , and ``goal``.


        **IF NO** ``grid`` **has been provided**, will request a fresh grid from :class:`.Pather`

        If no path is possible, will return ``None``

        ``sensitivity`` indicates how to slice the path,
        just like doing: ``result_path = path[::sensitivity]``
            where ``path`` is the return value from this function

        this is useful since in most use cases you wouldn't want
        to get each and every single point,

        getting every  n-``th`` point works better in practice

        `` large`` is a boolean that determines whether we are doing pathing with large unit sizes
        like Thor and Ultralisk. When it's false the pathfinding is using unit size 1, so if
        you want to a guarantee that a unit with size > 1 fits through the path then large should be True.

        ``smoothing`` tries to do a similar thing on the c side but to the maximum extent possible.
        it will skip all the waypoints it can if taking the straight line forward is better
        according to the influence grid

        Example:
            >>> my_grid = self.get_pyastar_grid()
            >>> # start / goal could be any tuple / Point2
            >>> st, gl = (50,75) , (100,100)
            >>> path = self.pathfind(start=st,goal=gl,grid=my_grid, large=False, smoothing=False, sensitivity=3)

        See Also:
            * :meth:`.MapData.get_pyastar_grid`
            * :meth:`.MapData.find_lowest_cost_points`

        """
        return self.pather.pathfind(
            start=start,
            goal=goal,
            grid=grid,
            large=large,
            smoothing=smoothing,
            sensitivity=sensitivity,
        )

    def pathfind_with_nyduses(
        self,
        start: Union[Tuple[float, float], Point2],
        goal: Union[Tuple[float, float], Point2],
        grid: Optional[ndarray] = None,
        large: bool = False,
        smoothing: bool = False,
        sensitivity: int = 1,
    ) -> Optional[Tuple[List[List[Point2]], Optional[List[int]]]]:
        """
        :rtype: Union[List[List[:class:`sc2.position.Point2`]], None]
        Will return the path with lowest cost (sum) given a weighted array (``grid``), ``start`` , and ``goal``.
        Returns a tuple where the first part is a list of path segments, second part is list of 2 tags for the
        nydus network units that were used.
        If one path segment is returned, it is a path from start node to goal node, no nydus node was used and
        the second part of the tuple is None.
        If two path segments are returned, the first one is from start node to a nydus network entrance,
        and the second one is from some other nydus network entrance to the goal node. The second part of the tuple
        includes first the tag of the nydus network node you should go into, and then the tag of the node you come
        out from.

        **IF NO** ``grid`` **has been provided**, will request a fresh grid from :class:`.Pather`

        If no path is possible, will return ``None``

        ``sensitivity`` indicates how to slice the path,
        just like doing: ``result_path = path[::sensitivity]``
            where ``path`` is the return value from this function

        this is useful since in most use cases you wouldn't want
        to get each and every single point,

        getting every  n-``th`` point works better in practice

        `` large`` is a boolean that determines whether we are doing pathing with large unit sizes
        like Thor and Ultralisk. When it's false the pathfinding is using unit size 1, so if
        you want to a guarantee that a unit with size > 1 fits through the path then large should be True.

        ``smoothing`` tries to do a similar thing on the c side but to the maximum extent possible.
        it will skip all the waypoints it can if taking the straight line forward is better
        according to the influence grid

        Example:
            >>> my_grid = self.get_pyastar_grid()
            >>> # start / goal could be any tuple / Point2
            >>> st, gl = (50,75) , (100,100)
            >>> path = self.pathfind(start=st,goal=gl,grid=my_grid, large=False, smoothing=False, sensitivity=3)

        See Also:
            * :meth:`.MapData.get_pyastar_grid`
            * :meth:`.MapData.find_lowest_cost_points`

        """
        return self.pather.pathfind_with_nyduses(
            start=start,
            goal=goal,
            grid=grid,
            large=large,
            smoothing=smoothing,
            sensitivity=sensitivity,
        )

    def add_cost(
        self,
        position: Tuple[float, float],
        radius: float,
        grid: ndarray,
        weight: float = 100,
        safe: bool = True,
        initial_default_weights: float = 0,
    ) -> ndarray:
        """
        :rtype: numpy.ndarray

        Will add cost to a `circle-shaped` area with a center ``position`` and radius ``radius``

        weight of 100

        Warning:
            When ``safe=False`` the Pather will not adjust illegal values below 1 which could result in a crash`

        See Also:
            * :meth:`.MapData.add_cost_to_multiple_grids`

        """
        return self.pather.add_cost(
            position=position,
            radius=radius,
            arr=grid,
            weight=weight,
            safe=safe,
            initial_default_weights=initial_default_weights,
        )

    def add_cost_to_multiple_grids(
        self,
        position: Tuple[float, float],
        radius: float,
        grids: List[ndarray],
        weight: float = 100,
        safe: bool = True,
        initial_default_weights: float = 0,
    ) -> List[ndarray]:
        """
        :rtype: List[numpy.ndarray]

        Like ``add_cost``, will add cost to a `circle-shaped` area with a center ``position`` and radius ``radius``
        Use this one for performance reasons if adding identical cost to multiple grids, so that the disk is only
        calculated once.

        Example:
            >>> air_grid = self.get_clean_air_grid()
            >>> ground_grid = self.get_pyastar_grid()
            >>> # commented out for doc test
            >>> # air_grid, ground_grid = self.add_cost_to_multiple_grids(
            >>> #    position=self.bot.game_info.map_center, radius=5, grids=[air_grid, ground_grid], weight=10)

        Warning:
            When ``safe=False`` the Pather will not adjust illegal values below 1 which could result in a crash`

        Tip:
            Performance against using `add_cost` for multiple grids, averaged over 1000 iterations
            For `add_cost` the method was called once per grid

            2 grids `add_cost_to_multiple_grids`: 188.18 µs ± 12.73 ns per loop
            2 grids `add_cost`                  : 229.95 µs ± 37.53 ns per loop

            3 grids `add_cost_to_multiple_grids`: 199.15 µs ± 21.86 ns per loop
            3 grids `add_cost`                  : 363.44 µs ± 80.89 ns per loop

            4 grids `add_cost_to_multiple_grids`: 222.34 µs ± 26.79 ns per loop
            4 grids `add_cost`                  : 488.94 µs ± 87.64 ns per loop

        """
        return self.pather.add_cost_to_multiple_grids(
            position=position,
            radius=radius,
            arrays=grids,
            weight=weight,
            safe=safe,
            initial_default_weights=initial_default_weights,
        )

    """Utility methods"""

    def save(self, filename):
        """

        Save Plot to a file, much like ``plt.save(filename)``

        """
        self.debugger.save(filename=filename)

    def show(self):
        """

        Calling debugger to show, just like ``plt.show()``  but in case there will be changes in debugger,

        This method will always be compatible

        """
        self.debugger.show()

    def close(self):
        """
        Close an opened plot, just like ``plt.close()``  but in case there will be changes in debugger,

        This method will always be compatible

        """
        self.debugger.close()

    @staticmethod
    def indices_to_points(
        indices: Union[ndarray, Tuple[ndarray, ndarray]]
    ) -> Set[Union[Tuple[float, float], Point2]]:
        """
        :rtype: :class:`.set` (Union[:class:`.tuple` (:class:`.int`, :class:`.int`), :class:`sc2.position.Point2`)

        Convert indices to a set of points(``tuples``, not ``Point2`` )

        Will only work when both dimensions are of same length

        """

        return set([(indices[0][i], indices[1][i]) for i in range(len(indices[0]))])

    @staticmethod
    def points_to_indices(
        points: Union[Set[Point2], List[Point2]]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        :rtype: Tuple[numpy.ndarray, numpy.ndarray]

        Convert a set / list of points to a tuple of two 1d numpy arrays

        """
        return np.array([p[0] for p in points]), np.array([p[1] for p in points])

    def points_to_numpy_array(
        self, points: Union[Set[Point2], List[Point2]], default_value: int = 1
    ) -> ndarray:
        """
        :rtype: numpy.ndarray

        Convert points to numpy ndarray

        Caution:
                Will handle safely(by ignoring) points that are ``out of bounds``, without warning
        """
        rows, cols = self.path_arr.shape
        # transpose so we can index into it with x, y instead of y, x
        arr = np.zeros((cols, rows), dtype=np.uint8)
        if isinstance(points, set):
            points = list(points)

        def in_bounds_x(x_):
            width = arr.shape[0] - 1
            if 0 < x_ < width:
                return x_
            return 0

        def in_bounds_y(y_):
            height = arr.shape[1] - 1
            if 0 < y_ < height:
                return y_
            return 0

        x_vec = np.vectorize(in_bounds_x)
        y_vec = np.vectorize(in_bounds_y)
        indices = self.points_to_indices(points)
        x = x_vec(indices[0])
        y = y_vec(indices[1])
        arr[x, y] = default_value
        return arr

    @staticmethod
    def distance(p1: Point2, p2: Point2) -> float:
        """
        :rtype: float64

        Euclidean distance
        """
        return math.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)

    @staticmethod
    def distance_squared(p1: Point2, p2: Point2) -> float:
        """
        :rtype: float64

        Euclidean distance squared
        """
        return (p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2

    @staticmethod
    def closest_node_idx(
        node: Union[Point2, ndarray], nodes: Union[List[Tuple[int, int]], ndarray]
    ) -> int:
        """
        :rtype: int

        Given a list of ``nodes``  and a single ``node`` ,

        will return the index of the closest node in the list to ``node``

        """
        if isinstance(nodes, list):
            iter = chain.from_iterable(nodes)
            nodes = np.fromiter(
                iter, dtype=type(nodes[0][0]), count=len(nodes) * 2
            ).reshape((-1, 2))

        closest_index = distance.cdist([node], nodes, "sqeuclidean").argmin()
        return closest_index

    def closest_towards_point(
        self, points: List[Point2], target: Union[Point2, tuple]
    ) -> Point2:
        """
        :rtype: :class:`sc2.position.Point2`

        Given a list/set of points, and a target,

        will return the point that is closest to that target

        Example:
                Calculate a position for tanks in direction to the enemy forces
                passing in the Area's corners as points and enemy army's location as target

                >>> enemy_army_position = (50,50)
                >>> my_base_location = self.bot.townhalls[0].position
                >>> my_region = self.where_all(my_base_location)[0]
                >>> best_siege_spot = self.closest_towards_point(points=my_region.corner_points, target=enemy_army_position)
                >>> best_siege_spot
                (49, 52)

        """

        if not isinstance(points, (list, ndarray)):
            logger.warning(type(points))

        return points[self.closest_node_idx(node=target, nodes=points)]

    """Query methods"""

    def region_connectivity_all_paths(
        self,
        start_region: Region,
        goal_region: Region,
        not_through: Optional[List[Region]] = None,
    ) -> List[List[Region]]:
        """
        :param start_region: :mod:`.Region`
        :param goal_region: :mod:`.Region`
        :param not_through: Optional[List[:mod:`.Region`]]
        :rtype: List[List[:mod:`.Region`]]

        Returns all possible paths through all :mod:`.Region` (via ramps),

        can exclude a region by passing it in a not_through list

        """
        all_paths = self.pather.find_all_paths(start=start_region, goal=goal_region)
        filtered_paths = all_paths.copy()
        if not_through is not None:
            for path in all_paths:
                if any([x in not_through for x in path]):
                    filtered_paths.remove(path)
            all_paths = filtered_paths
        return all_paths

    @lru_cache(200)
    def where_all(
        self, point: Union[Point2, tuple]
    ) -> List[Union[Region, ChokeArea, VisionBlockerArea, MDRamp]]:
        """
        :rtype: List[Union[:class:`.Region`, :class:`.ChokeArea`, :class:`.VisionBlockerArea`, :class:`.MDRamp`]]

        Will return a list containing all :class:`.Polygon` that occupy the given point.

        If a :class:`.Region` exists in that list, it will be the first item

        Caution:
                Not all points on the map belong to a :class:`.Region` ,
                some are in ``border`` polygons such as :class:`.MDRamp`


        Example:
                >>> # query in which region is the enemy main
                >>> position = self.bot.enemy_start_locations[0].position
                >>> all_polygon_areas_in_position = self.where_all(position)
                >>> all_polygon_areas_in_position
                [Region 4]

                >>> enemy_main_base_region = all_polygon_areas_in_position[0]
                >>> enemy_main_base_region
                Region 4

                >>> # now it is very easy to know which region is the enemy's natural
                >>> # connected_regions is a property of a Region
                >>> enemy_natural_region = enemy_main_base_region.connected_regions[0]
                >>> # will return Region 1 or 6 for goldenwall depending on starting position


        Tip:

            *avg performance*

            * :class:`.Region` query 21.5 µs ± 652 ns per loop (mean ± std. dev. of 7 runs, 10000 loops each)
            * :class:`.ChokeArea` ``query 18 µs`` ± 1.25 µs per loop (mean ± std. dev. of 7 runs, 100000 loops each)
            * :class:`.MDRamp` query  22 µs ± 982 ns per loop (mean ± std. dev. of 7 runs, 10000 loops each)


        """
        results = []
        if isinstance(point, Point2):
            point = point.rounded
        if isinstance(point, tuple):
            point = int(point[0]), int(point[1])

        for region in self.regions.values():
            if region.is_inside_point(point):
                results.append(region)
        for choke in self.map_chokes:
            if choke.is_inside_point(point):
                results.append(choke)
        # assert (len(list(set(results))) == len(results)), f"results{results},  list(set(results)){list(set(results))}"
        return results

    def where(
        self, point: Union[Point2, tuple]
    ) -> Union[Region, MDRamp, ChokeArea, VisionBlockerArea]:
        """
        :rtype: Union[:mod:`.Region`, :class:`.ChokeArea`, :class:`.VisionBlockerArea`, :class:`.MDRamp`]

        Will query a point on the map and will return the first result in the following order:

            * :class:`.Region`
            * :class:`.MDRamp`
            * :class:`.ChokeArea`

        Tip:

            *avg performance*

            * :class:`.Region` query 7.09 µs ± 329 ns per loop (mean ± std. dev. of 7 runs, 100000 loops each)
            * :class:`.ChokeArea` query  17.9 µs ± 1.22 µs per loop (mean ± std. dev. of 7 runs, 100000 loops each)
            * :class:`.MDRamp` ``query 11.7 µs`` ± 1.13 µs per loop (mean ± std. dev. of 7 runs, 100000 loops each)

        """
        if isinstance(point, Point2):
            point = point.rounded
        if isinstance(point, tuple):
            point = int(point[0]), int(point[1])

        for region in self.regions.values():
            if region.is_inside_point(point):
                return region
        for choke in self.map_chokes:
            if choke.is_inside_point(point):
                return choke

    @lru_cache(100)
    def in_region_p(self, point: Union[Point2, tuple]) -> Optional[Region]:
        """
        :rtype: Optional[:class:`.Region`]

        Will query if a point is in, and in which Region using Set of Points <fast>

        Tip:
            time benchmark 4.35 µs ± 27.5 ns per loop (mean ± std. dev. of 7 runs, 100000 loops each)

            as long as polygon points is of type :class:`.set`, not :class:`.list`

        """
        if isinstance(point, Point2):
            point = point.rounded
        if isinstance(point, tuple):
            point = int(point[0]), int(point[1])
        for region in self.regions.values():
            if region.is_inside_point(point):
                return region

    """Compile methods"""

    @staticmethod
    def _get_overlapping_chokes(
        local_chokes: List[CMapChoke],
        areas: Union[List[MDRamp], List[Union[MDRamp, VisionBlockerArea]]],
    ) -> Set[int]:
        li = []
        for area in areas:
            li.append(
                get_sets_with_mutual_elements(list_mdchokes=local_chokes, area=area)
            )
        result = []
        for minili in li:
            result.extend(minili)
        return set(result)

    def _clean_polys(self) -> None:
        i = 0
        while i < len(self.polygons):
            pol = self.polygons[i]
            if not MAX_REGION_AREA > pol.area > MIN_REGION_AREA:
                self.polygons.pop(i)
                continue
            if pol.is_choke:
                ramp_found = False
                for area in pol.areas:
                    if isinstance(area, MDRamp):
                        ramp_found = True
                        break
                if ramp_found:
                    self.polygons.pop(i)
                    continue

            i += 1

    @progress_wrapped(
        estimated_time=0,
        desc=f"\u001b[32m Version {__version__} Map Compilation Progress \u001b[37m",
    )
    def _compile_map(self) -> None:
        self._calc_grid()
        self._calc_regions()
        self._calc_vision_blockers()
        self._set_map_ramps()
        self._clean_polys()
        self._calc_chokes()
        self._calc_poly_areas()
        for ramp in self.map_ramps:
            ramp.set_regions()
        self.pather.set_connectivity_graph()
        self.connectivity_graph = self.pather.connectivity_graph

    def _calc_grid(self) -> None:
        # converting the placement grid to our own kind of grid
        # cleaning the grid and then searching for 2x2 patterned regions
        grid = binary_fill_holes(self.placement_arr).astype(int)
        # for our grid,  mineral walls are considered as a barrier between regions
        for point in self.resource_blockers:
            grid[int(point[1])][int(point[0])] = 0
            for n in point.neighbors4:
                point_ = Point2((n.rounded[0], n.rounded[1]))
                if point_[0] < grid.shape[1] and point_[1] < grid.shape[0]:
                    grid[int(point_[1])][int(point_[0])] = 0

        s = generate_binary_structure(BINARY_STRUCTURE, BINARY_STRUCTURE)
        labeled_array, num_features = ndlabel(grid, structure=s)

        # for some operations the array must have same numbers or rows and cols,  adding
        # zeros to fix that
        # rows, cols = labeled_array.shape
        # self.region_grid = np.append(labeled_array, np.zeros((abs(cols - rows), cols)), axis=0)
        self.region_grid = labeled_array.astype(int)
        self.regions_labels = np.unique(self.region_grid)
        vb_points = self._vision_blockers

        # some maps has no vision blockers
        if len(vb_points):
            vision_blockers_indices = self.points_to_indices(vb_points)
            rows, cols = self.path_arr.shape
            vision_blockers_array = np.zeros((cols, rows), dtype="int")
            vision_blockers_array[vision_blockers_indices] = 1
            vb_labeled_array, vb_num_features = ndlabel(vision_blockers_array)
            self.vision_blockers_grid = vb_labeled_array
            self.vision_blockers_labels = np.unique(vb_labeled_array)

    def _calc_poly_areas(self) -> None:
        """
        Check for `Polygon` types that exist in other polygons
        For example a choke or ramp may exist in a region, so should be added as an "area"
        """
        self.extended_array_matrix = np.ones(
            (
                len(self.polygons),
                self.bot.game_info.map_size[0],
                self.bot.game_info.map_size[1],
            )
        )
        for i, poly in enumerate(self.polygons):
            self.extended_array_matrix[i] = poly.extended_array

        for poly in self.polygons:
            poly_in_areas: np.ndarray = (
                self.extended_array_matrix[
                    :, poly.outer_perimeter[:, 0], poly.outer_perimeter[:, 1]
                ]
                == 1
            )
            area_ids: np.ndarray = np.unique(np.where(poly_in_areas)[0])
            for idx in area_ids:
                area = self.polygons[idx]
                if poly != area:
                    poly.areas.append(area)

    def _set_map_ramps(self):
        # some ramps coming from burnysc2 have broken data and the bottom_center and top_center
        # may even be the same. by removing them they should be tagged as chokes in the c extension
        # if they really are ones
        viable_ramps = list(
            filter(
                lambda x: x.bottom_center.distance_to(x.top_center) >= 1,
                self.bot.game_info.map_ramps,
            )
        )
        self.map_ramps = [
            MDRamp(map_data=self, ramp=r, array=self.points_to_numpy_array(r.points))
            for r in viable_ramps
        ]

    def _calc_vision_blockers(self) -> None:
        # compute VisionBlockerArea

        for i in range(len(self.vision_blockers_labels)):
            vb_arr = np.where(self.vision_blockers_grid == i, 1, 0)
            vba = VisionBlockerArea(map_data=self, array=vb_arr)
            if vba.area <= 200:
                self.map_vision_blockers.append(vba)
                areas = self.where_all(vba.center)
                if len(areas) > 0:
                    for area in areas:
                        if area is not vba:
                            vba.areas.append(area)
            else:
                self.polygons.pop(self.polygons.index(vba))

    def _calc_chokes(self) -> None:
        # compute ChokeArea
        self.map_chokes = self.map_ramps.copy()
        self.map_chokes.extend(self.map_vision_blockers)

        overlapping_choke_ids = self._get_overlapping_chokes(
            local_chokes=self.c_ext_map.chokes, areas=self.map_chokes
        )
        chokes = [c for c in self.c_ext_map.chokes if c.id not in overlapping_choke_ids]

        for choke in chokes:

            points = [Point2(p) for p in choke.pixels]
            if len(points) > 0:
                new_choke_array = self.points_to_numpy_array(points)
                cm = center_of_mass(new_choke_array)
                cm = int(cm[0]), int(cm[1])
                areas = self.where_all(cm)

                new_choke = RawChoke(
                    map_data=self, array=new_choke_array, raw_choke=choke
                )
                for area in areas:

                    if isinstance(area, Region):
                        area.region_chokes.append(new_choke)
                        new_choke.areas.append(area)
                    if (
                        area.is_choke
                        and not area.is_ramp
                        and not area.is_vision_blocker
                    ):
                        self.polygons.remove(new_choke)
                        area.points.update(new_choke.points)
                        new_choke = None
                        break

                if new_choke:
                    self.map_chokes.append(new_choke)
            else:  # pragma: no cover
                logger.debug(f" [{self.map_name}] Cant add {choke} with 0 points")

    def _calc_regions(self) -> None:
        # compute Region

        label_count = 0
        for i in range(len(self.regions_labels)):
            region = Region(
                array=np.where(self.region_grid == i, 1, 0).T,
                label=i,
                map_data=self,
                map_expansions=self.base_locations,
            )
            if MAX_REGION_AREA > region.area > MIN_REGION_AREA:
                region.label = label_count
                self.regions[label_count] = region
                label_count += 1

    """Plot methods"""

    def draw_influence_in_game(
        self,
        grid: ndarray,
        lower_threshold: int = 1,
        upper_threshold: int = 1000,
        color: Tuple[int, int, int] = (201, 168, 79),
        size: int = 13,
    ) -> None:
        """
        :rtype: None
        Draws influence (cost) values of a grid in game.

        Caution:
            Setting the lower threshold too low impacts performance since almost every value will get drawn.

            It's recommended that this is set to the relevant grid's default weight value.

        Example:
                >>> self.ground_grid = self.get_pyastar_grid(default_weight=1)
                >>> self.ground_grid = self.add_cost((100, 100), radius=15, grid=self.ground_grid, weight=50)
                >>> # self.draw_influence_in_game(self.ground_grid, lower_threshold=1) # commented out for doctest

        See Also:
            * :meth:`.MapData.get_pyastar_grid`
            * :meth:`.MapData.get_climber_grid`
            * :meth:`.MapData.get_clean_air_grid`
            * :meth:`.MapData.get_air_vs_ground_grid`
            * :meth:`.MapData.add_cost`

        """
        self.debugger.draw_influence_in_game(
            self.bot, grid, lower_threshold, upper_threshold, color, size
        )

    def plot_map(
        self, fontdict: dict = None, save: Optional[bool] = None, figsize: int = 20
    ) -> None:
        """

        Plot map (does not ``show`` or ``save``)

        """
        if save is not None:
            logger.warning(
                CustomDeprecationWarning(oldarg="save", newarg="self.save()")
            )
        import inspect

        logger.error(f"{inspect.stack()[1]}")
        self.debugger.plot_map(fontdict=fontdict, figsize=figsize)

    def plot_influenced_path(
        self,
        start: Union[Tuple[float, float], Point2],
        goal: Union[Tuple[float, float], Point2],
        weight_array: ndarray,
        large: bool = False,
        smoothing: bool = False,
        name: Optional[str] = None,
        fontdict: dict = None,
    ) -> None:
        """

        A useful debug utility method for experimenting with the :mod:`.Pather` module

        """

        self.debugger.plot_influenced_path(
            start=start,
            goal=goal,
            weight_array=weight_array,
            large=large,
            smoothing=smoothing,
            name=name,
            fontdict=fontdict,
        )

    def plot_influenced_path_nydus(
        self,
        start: Union[Tuple[float, float], Point2],
        goal: Union[Tuple[float, float], Point2],
        weight_array: ndarray,
        large: bool = False,
        smoothing: bool = False,
        name: Optional[str] = None,
        fontdict: dict = None,
    ) -> None:
        """

        A useful debug utility method for experimenting with the :mod:`.Pather` module

        """

        self.debugger.plot_influenced_path_nydus(
            start=start,
            goal=goal,
            weight_array=weight_array,
            large=large,
            smoothing=smoothing,
            name=name,
            fontdict=fontdict,
        )

    def _plot_regions(self, fontdict: Dict[str, Union[str, int]]) -> None:
        return self.debugger.plot_regions(fontdict=fontdict)

    def _plot_vision_blockers(self) -> None:
        self.debugger.plot_vision_blockers()

    def _plot_normal_resources(self) -> None:
        # todo: account for gold minerals and rich gas
        self.debugger.plot_normal_resources()

    def _plot_chokes(self) -> None:
        self.debugger.plot_chokes()

    def __repr__(self) -> str:
        return f"<MapData[{self.version}][{self.bot.game_info.map_name}][{self.bot}]>"
