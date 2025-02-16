"""Handle pathing information.

This manager handles path finding and coordinates with GridManager for grid-related
operations.
"""
from typing import TYPE_CHECKING, Any, Dict, List, Union

import numpy as np
from cython_extensions import cy_point_below_value
from map_analyzer import MapData
from sc2.position import Point2
from scipy import spatial
from scipy.spatial import KDTree

from ares.consts import (
    DANGER_THRESHOLD,
    DANGER_TILES,
    DEBUG,
    PATHING_GRID,
    ManagerName,
    ManagerRequestType,
)
from ares.managers.manager import Manager
from ares.managers.manager_mediator import IManagerMediator, ManagerMediator

if TYPE_CHECKING:
    from ares import AresBot


class PathManager(Manager, IManagerMediator):
    """Manager for handling paths.

    All unit pathing should be done here
    This also exposes SC2MapAnalyzer api_reference through `self.map_data`
    """

    def manager_request(
        self,
        receiver: ManagerName,
        request: ManagerRequestType,
        reason: str = None,
        **kwargs,
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
        Any
            The result of the request
        """
        return self.manager_requests_dict[request](kwargs)

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
        """
        super().__init__(ai, config, mediator)
        self.debug: bool = self.config[DEBUG]
        self.map_data: MapData = MapData(ai, arcade=self.ai.arcade_mode)

        self.whole_map: List[List[int]] = [
            [x, y]
            for x in range(self.ai.game_info.map_size[0])
            for y in range(self.ai.game_info.map_size[1])
        ]
        self.whole_map_tree: KDTree = KDTree(self.whole_map)
        # vague attempt at not recalculating np.argwhere for danger tiles
        self.calculated_danger_tiles: List[Dict[str, Union[np.ndarray, int]]] = []

        self.manager_requests_dict = {
            ManagerRequestType.GET_AIR_AVOIDANCE_GRID: lambda kwargs: (
                self.mediator.manager_request(
                    ManagerName.GRID_MANAGER,
                    ManagerRequestType.GET_AIR_AVOIDANCE_GRID,
                    **kwargs,
                )
            ),
            ManagerRequestType.FIND_LOW_PRIORITY_PATH: lambda kwargs: (
                self.find_low_priority_path(**kwargs)
            ),
            ManagerRequestType.FIND_LOWEST_COST_POINTS: lambda kwargs: (
                self.map_data.find_lowest_cost_points(**kwargs)
            ),
            ManagerRequestType.FIND_RAW_PATH: lambda kwargs: self.raw_pathfind(
                **kwargs
            ),
            ManagerRequestType.IS_POSITION_SAFE: lambda kwargs: self.is_position_safe(
                **kwargs
            ),
            ManagerRequestType.GET_CLOSEST_SAFE_SPOT: (
                lambda kwargs: self.find_closest_safe_spot(**kwargs)
            ),
            ManagerRequestType.GET_MAP_DATA: lambda kwargs: self.map_data,
            ManagerRequestType.GET_WHOLE_MAP_ARRAY: lambda kwargs: self.whole_map,
            ManagerRequestType.GET_WHOLE_MAP_TREE: lambda kwargs: self.whole_map_tree,
            ManagerRequestType.PATH_NEXT_POINT: lambda kwargs: (
                self.find_path_next_point(**kwargs)
            ),
        }

    async def update(self, iteration: int) -> None:
        """Keep track of everything.

        Parameters
        ----------
        iteration :
            The game iteration.
        """
        pass

    def find_closest_safe_spot(
        self, from_pos: Point2, grid: np.ndarray, radius: int = 11
    ) -> Point2:
        """Find the closest point with the lowest cost on a grid.

        Parameters
        ----------
        from_pos :
            Where the search starts from.
        grid :
            The grid to find the low cost point on.
        radius :
            How far away the safe point can be.

        Returns
        -------
        Point2 :
            The closest location with the lowest cost.
        """
        all_safe: np.ndarray = self.map_data.lowest_cost_points_array(
            from_pos, radius, grid
        )
        # type hint wants a numpy array but doesn't actually need one - this is faster
        all_dists = spatial.distance.cdist(all_safe, [from_pos], "sqeuclidean")
        min_index = np.argmin(all_dists)

        # safe because the shape of all_dists (N x 1) means argmin will return an int
        return Point2(all_safe[min_index])

    def find_furthest_safe_spot(
        self, from_pos: Point2, grid: np.ndarray, radius: int = 15
    ) -> Point2:
        """Find the furthest safe point from a given position.

        Parameters
        ----------
        from_pos :
            Where the search starts from.
        grid :
            The grid to find the low cost point on.
        radius :
            How far away the safe point can be.

        Returns
        -------
        Point2 :
            The furthest location with the lowest cost.
        """
        safe_spot = sorted(
            self.map_data.find_lowest_cost_points(from_pos, radius, grid),
            key=lambda spot: self.ai.distance_math_hypot(spot, from_pos),
        )[-1]

        return safe_spot

    def find_low_priority_path(
        self, start: Point2, target: Point2, grid: np.ndarray
    ) -> List[Point2]:
        """Find several points in a path.

        This way a unit can queue them up all at once for performance reasons.

        i.e. running drones from a base or sending an overlord to a new position.

        Notes
        -----
        This does not return every point in the path. Instead, it returns points spread
        along the path.

        Parameters
        ----------
        start :
            Start point of the path.
        target :
            Desired end point of the path.
        grid :
            The grid that should be used for pathing.

        Returns
        -------
        List[Point2] :
            List of points composing the path.
        """
        result: List[Point2] = self.map_data.pathfind(
            start, target, grid, sensitivity=4
        )

        if not result or len(result) < 10:
            return [target]

        idx = np.round(np.linspace(0, len(result) - 1, 8, dtype="int"))

        path: List[Point2] = [result[i] for i in idx]
        path.append(target)
        return path

    def find_path_next_point(
        self,
        start: Point2,
        target: Point2,
        grid: np.ndarray,
        sensitivity: int = 5,
        smoothing: bool = False,
        sense_danger: bool = True,
        danger_distance: int = 20.0,
        danger_threshold: float = 5.0,
    ) -> Point2:
        """Find the next point in a path.

        Parameters
        ----------
        start :
            Start point of the path.
        target :
            Desired end point of the path.
        grid :
            The grid that should be used for pathing.
        sensitivity :
            Amount of points that should be skipped in the full path between tiles that
            are returned.
        smoothing :
            Optional path smoothing where nodes are removed if it's possible to jump
            ahead some tiles in a straight line with a lower cost.
        sense_danger :
            Check to see if there are any dangerous tiles near the starting point. If
            this is True and there are no dangerous tiles near the starting point, the
            pathing query is skipped and the target is returned.
        danger_distance :
            How far away from the start to look for danger.
        danger_threshold :
            Minimum value for a tile to be considered dangerous.

        Returns
        -------
        Point2 :
            The next point in the path from the start to the target which may be the
            same as the target if it's safe.
        """
        if sense_danger:
            """
            Check the stored dictionaries to see if we've already computed danger tiles
            for a given array (pathing grid) and danger threshold. If we have, use the
            precomputed danger tiles, otherwise compute the tiles and store them.
            Initial check is for the same danger threshold, second check does an
            element-wise comparison of the stored array and the current array and then
            checks that each element of the comparison is True (indicating identical
            grids).
            """
            found = False
            for precalculated in self.calculated_danger_tiles:
                if precalculated[DANGER_THRESHOLD] == danger_threshold:
                    if (precalculated[PATHING_GRID] == grid).all():
                        dangers = precalculated[DANGER_TILES]
                        found = True
                        break
            if not found:
                # find all dangerous cells on the grid
                dangers = np.argwhere((grid >= danger_threshold) & (grid < np.inf))
                self.calculated_danger_tiles.append(
                    {
                        PATHING_GRID: grid.copy(),
                        DANGER_THRESHOLD: danger_threshold,
                        DANGER_TILES: dangers.copy(),
                    }
                )
            if dangers.shape[0] > 0:
                # get distance of the closest dangerous cell
                closest_danger_distance: float = spatial.distance.cdist(
                    [start], dangers
                ).min()
                # the closest danger is too far away, no need for pathing query
                if closest_danger_distance >= danger_distance:
                    return target
            # didn't find any danger at all
            else:
                return target

        path: List[Point2] = self.map_data.pathfind(
            start, target, grid, sensitivity=sensitivity, smoothing=smoothing
        )
        if not path or len(path) == 0:
            return target
        else:
            return path[0]

    def raw_pathfind(
        self, start: Point2, target: Point2, grid: np.ndarray, sensitivity: int
    ) -> List[Point2]:
        """Used for finding a full path, mostly for distance checks.

        Parameters
        ----------
        start :
            Start point of the path.
        target :
            Desired end point of the path.
        grid :
            The grid that should be used for pathing.
        sensitivity :
            Amount of points that should be skipped in the full path between tiles that
            are returned.

        Returns
        -------
        List[Point2] :
            List of points composing the path
        """
        return self.map_data.pathfind(start, target, grid, sensitivity=sensitivity)

    @staticmethod
    def is_position_safe(
        grid: np.ndarray,
        position: Point2,
        weight_safety_limit: float = 1.0,
    ) -> bool:
        """Check if the given position is considered dangerous.

        Parameters
        ----------
        grid :
            The grid to evaluate safety on.
        position :
            The position to check the safety of.
        weight_safety_limit :
            The maximum value the point can have on the grid to be considered safe.

        Returns
        -------
        bool :
            True if the position is considered safe, False otherwise.
        """
        return cy_point_below_value(grid, position.rounded, weight_safety_limit)
