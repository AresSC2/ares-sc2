from typing import List, Optional, Tuple, TYPE_CHECKING

import numpy as np

from loguru import logger
from numpy import ndarray
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2

from MapAnalyzer.exceptions import OutOfBoundsException, PatherNoPointsException
from MapAnalyzer.Region import Region
from MapAnalyzer.utils import change_destructable_status_in_grid
from .cext import astar_path, astar_path_with_nyduses
from .destructibles import *

if TYPE_CHECKING:
    from MapAnalyzer.MapData import MapData


def _bounded_circle(center, radius, shape):
    xx, yy = np.ogrid[: shape[0], : shape[1]]
    circle = (xx - center[0]) ** 2 + (yy - center[1]) ** 2
    return np.nonzero(circle <= radius ** 2)


def draw_circle(c, radius, shape=None):
    center = np.array(c)
    upper_left = np.ceil(center - radius).astype(int)
    lower_right = np.floor(center + radius).astype(int) + 1

    if shape is not None:
        # Constrain upper_left and lower_right by shape boundary.
        upper_left = np.maximum(upper_left, 0)
        lower_right = np.minimum(lower_right, np.array(shape))

    shifted_center = center - upper_left
    bounding_shape = lower_right - upper_left

    rr, cc = _bounded_circle(shifted_center, radius, bounding_shape)
    return rr + upper_left[0], cc + upper_left[1]


class MapAnalyzerPather:
    """"""

    def __init__(self, map_data: "MapData") -> None:
        self.map_data = map_data

        self.connectivity_graph = None  # set later by MapData

        self._set_default_grids()
        self.terrain_height = self.map_data.terrain_height.copy().T

    def _set_default_grids(self):
        # need to consider the placement arr because our base minerals, geysers and townhall
        # are not pathable in the pathing grid
        # we manage those manually so they are accurate through the game
        self.default_grid = np.fmax(
            self.map_data.path_arr, self.map_data.placement_arr
        ).T

        # Fixing platforms on Submarine which reapers can climb onto not being pathable
        # Don't use the entire name because we also use the modified maps
        # with different names
        if "Submarine" in self.map_data.map_name:
            self.default_grid[116, 43] = 1
            self.default_grid[51, 120] = 1

        self.default_grid_nodestr = self.default_grid.copy()

        self.destructables_included = {}
        self.minerals_included = {}

        # set rocks and mineral walls to pathable in the beginning
        # these will be set nonpathable when updating grids for the destructables
        # that still exist
        for dest in self.map_data.bot.destructables:
            self.destructables_included[dest.position] = dest
            if (
                "unbuildable" not in dest.name.lower()
                and "acceleration" not in dest.name.lower()
            ):
                change_destructable_status_in_grid(self.default_grid, dest, 0)
                change_destructable_status_in_grid(self.default_grid_nodestr, dest, 1)

        # set each geyser as non pathable, these don't update during the game
        for geyser in self.map_data.bot.vespene_geyser:
            left_bottom = geyser.position.offset((-1.5, -1.5))
            x_start = int(left_bottom[0])
            y_start = int(left_bottom[1])
            x_end = int(x_start + 3)
            y_end = int(y_start + 3)
            self.default_grid[x_start:x_end, y_start:y_end] = 0
            self.default_grid_nodestr[x_start:x_end, y_start:y_end] = 0

        for mineral in self.map_data.bot.mineral_field:
            self.minerals_included[mineral.position] = mineral
            x1 = int(mineral.position[0])
            x2 = x1 - 1
            y = int(mineral.position[1])

            self.default_grid[x1, y] = 0
            self.default_grid[x2, y] = 0
            self.default_grid_nodestr[x1, y] = 0
            self.default_grid_nodestr[x2, y] = 0

    def set_connectivity_graph(self):
        connectivity_graph = {}
        for region in self.map_data.regions.values():
            if connectivity_graph.get(region) is None:
                connectivity_graph[region] = []
            for connected_region in region.connected_regions:
                if connected_region not in connectivity_graph.get(region):
                    connectivity_graph[region].append(connected_region)
        self.connectivity_graph = connectivity_graph

    def find_all_paths(
        self, start: Region, goal: Region, path: Optional[List[Region]] = None
    ) -> List[List[Region]]:
        if path is None:
            path = []
        graph = self.connectivity_graph
        path = path + [start]
        if start == goal:
            return [path]
        if start not in graph:
            return []
        paths = []
        for node in graph[start]:
            if node not in path:
                newpaths = self.find_all_paths(node, goal, path)
                for newpath in newpaths:
                    paths.append(newpath)
        return paths

    def _add_non_pathables_ground(
        self, grid: ndarray, include_destructables: bool = True
    ) -> ndarray:
        ret_grid = grid.copy()
        nonpathables = self.map_data.bot.structures.not_flying
        nonpathables.extend(self.map_data.bot.enemy_structures.not_flying)
        nonpathables = nonpathables.filter(
            lambda x: (x.type_id != UnitTypeId.SUPPLYDEPOTLOWERED or x.is_active)
            and (x.type_id != UnitTypeId.CREEPTUMOR or not x.is_ready)
        )

        for obj in nonpathables:
            size = 1
            if obj.type_id in buildings_2x2:
                size = 2
            elif obj.type_id in buildings_3x3:
                size = 3
            elif obj.type_id in buildings_5x5:
                size = 5
            left_bottom = obj.position.offset((-size / 2, -size / 2))
            x_start = int(left_bottom[0])
            y_start = int(left_bottom[1])
            x_end = int(x_start + size)
            y_end = int(y_start + size)

            ret_grid[x_start:x_end, y_start:y_end] = 0

            # townhall sized buildings should have their corner spots pathable
            if size == 5:
                ret_grid[x_start, y_start] = 1
                ret_grid[x_start, y_end - 1] = 1
                ret_grid[x_end - 1, y_start] = 1
                ret_grid[x_end - 1, y_end - 1] = 1

        if len(self.minerals_included) != self.map_data.bot.mineral_field.amount:

            new_positions = set(m.position for m in self.map_data.bot.mineral_field)
            old_mf_positions = set(self.minerals_included)

            missing_positions = old_mf_positions - new_positions
            for mf_position in missing_positions:
                x1 = int(mf_position[0])
                x2 = x1 - 1
                y = int(mf_position[1])

                ret_grid[x1, y] = 1
                ret_grid[x2, y] = 1

                self.default_grid[x1, y] = 1
                self.default_grid[x2, y] = 1

                self.default_grid_nodestr[x1, y] = 1
                self.default_grid_nodestr[x2, y] = 1

                del self.minerals_included[mf_position]

        if (
            include_destructables
            and len(self.destructables_included)
            != self.map_data.bot.destructables.amount
        ):
            new_positions = set(d.position for d in self.map_data.bot.destructables)
            old_dest_positions = set(self.destructables_included)
            missing_positions = old_dest_positions - new_positions

            for dest_position in missing_positions:
                dest = self.destructables_included[dest_position]
                change_destructable_status_in_grid(ret_grid, dest, 1)
                change_destructable_status_in_grid(self.default_grid, dest, 1)

                del self.destructables_included[dest_position]

        return ret_grid

    def find_eligible_point(
        self,
        point: Tuple[float, float],
        grid: np.ndarray,
        terrain_height: np.ndarray,
        max_distance: float,
    ) -> Optional[Tuple[int, int]]:
        """
        User may give a point that is in a nonpathable grid cell, for example inside a building or
        inside rocks. The desired behavior is to move the point a bit so for example we can start or finish
        next to the building the original point was inside of.
        To make sure that we don't accidentally for example offer a point that is on low ground when the
        first target was on high ground, we first try to find a point that maintains the terrain height.
        After that we check for points on other terrain heights.
        """
        point = (int(point[0]), int(point[1]))

        if grid[point] == np.inf:
            target_height = terrain_height[point]
            disk = tuple(draw_circle(point, max_distance, shape=grid.shape))
            # Using 8 for the threshold in case there is some variance on the same level
            # Proper levels have a height difference of 16
            same_height_cond = np.logical_and(
                np.abs(terrain_height[disk] - target_height) < 8, grid[disk] < np.inf
            )

            if np.any(same_height_cond):
                possible_points = np.column_stack(
                    (disk[0][same_height_cond], disk[1][same_height_cond])
                )
                closest_point_index = np.argmin(
                    np.sum((possible_points - point) ** 2, axis=1)
                )
                return tuple(possible_points[closest_point_index])
            else:
                diff_height_cond = grid[disk] < np.inf
                if np.any(diff_height_cond):
                    possible_points = np.column_stack(
                        (disk[0][diff_height_cond], disk[1][diff_height_cond])
                    )
                    closest_point_index = np.argmin(
                        np.sum((possible_points - point) ** 2, axis=1)
                    )
                    return tuple(possible_points[closest_point_index])
                else:
                    return None
        return point

    def lowest_cost_points_array(
        self, from_pos: tuple, radius: float, grid: np.ndarray
    ) -> Optional[np.ndarray]:
        """For use with evaluations that use numpy arrays
            example: # Closest point to unit furthest from target
                    distances = cdist([[unitpos, targetpos]], lowest_points, "sqeuclidean")
                    lowest_points[(distances[0] - distances[1]).argmin()]
        - 140 µs per loop
        """

        disk = tuple(draw_circle(from_pos, radius, shape=grid.shape))
        if len(disk[0]) == 0:
            return None

        arrmin = np.min(grid[disk])
        cond = grid[disk] == arrmin
        return np.column_stack((disk[0][cond], disk[1][cond]))

    def find_lowest_cost_points(
        self, from_pos: Point2, radius: float, grid: np.ndarray
    ) -> Optional[List[Point2]]:
        lowest = self.lowest_cost_points_array(from_pos, radius, grid)

        if lowest is None:
            return None

        return list(map(Point2, lowest))

    def get_base_pathing_grid(self, include_destructables: bool = True) -> ndarray:
        if include_destructables:
            return self.default_grid.copy()
        else:
            return self.default_grid_nodestr.copy()

    def get_climber_grid(
        self, default_weight: float = 1, include_destructables: bool = True
    ) -> ndarray:
        """Grid for units like reaper / colossus"""
        grid = self.get_base_pathing_grid(include_destructables)
        grid = np.where(self.map_data.c_ext_map.climber_grid != 0, 1, grid)
        grid = self._add_non_pathables_ground(
            grid=grid, include_destructables=include_destructables
        )
        grid = np.where(grid != 0, default_weight, np.inf).astype(np.float32)
        return grid

    def get_clean_air_grid(self, default_weight: float = 1) -> ndarray:
        clean_air_grid = np.zeros(shape=self.default_grid.shape).astype(np.float32)
        area = self.map_data.bot.game_info.playable_area
        clean_air_grid[
            area.x : (area.x + area.width), area.y : (area.y + area.height)
        ] = 1
        return np.where(clean_air_grid == 1, default_weight, np.inf).astype(np.float32)

    def get_air_vs_ground_grid(self, default_weight: float) -> ndarray:
        grid = self.get_pyastar_grid(
            default_weight=default_weight, include_destructables=True
        )
        # set non pathable points inside map bounds to value 1
        area = self.map_data.bot.game_info.playable_area
        start_x = area.x
        end_x = area.x + area.width
        start_y = area.y
        end_y = area.y + area.height
        grid[start_x:end_x, start_y:end_y] = np.where(
            grid[start_x:end_x, start_y:end_y] == np.inf, 1, default_weight
        )

        return grid

    def get_pyastar_grid(
        self, default_weight: float = 1, include_destructables: bool = True
    ) -> ndarray:
        grid = self.get_base_pathing_grid(include_destructables)
        grid = self._add_non_pathables_ground(
            grid=grid, include_destructables=include_destructables
        )

        grid = np.where(grid != 0, default_weight, np.inf).astype(np.float32)
        return grid

    def pathfind(
        self,
        start: Tuple[float, float],
        goal: Tuple[float, float],
        grid: Optional[ndarray] = None,
        large: bool = False,
        smoothing: bool = False,
        sensitivity: int = 1,
    ) -> Optional[List[Point2]]:
        if grid is None:
            logger.warning("Using the default pyastar grid as no grid was provided.")
            grid = self.get_pyastar_grid()

        if start is not None and goal is not None:
            start = round(start[0]), round(start[1])
            start = self.find_eligible_point(start, grid, self.terrain_height, 10)
            goal = round(goal[0]), round(goal[1])
            goal = self.find_eligible_point(goal, grid, self.terrain_height, 10)
        else:
            logger.warning(PatherNoPointsException(start=start, goal=goal))
            return None

        # find_eligible_point didn't find any pathable nodes nearby
        if start is None or goal is None:
            return None

        path = astar_path(grid, start, goal, large, smoothing)

        if path is not None:
            # Remove the starting point from the path.
            # Make sure the goal node is the last node even if we are
            # skipping points
            complete_path = list(map(Point2, path))
            skipped_path = complete_path[0:-1:sensitivity]
            if skipped_path:
                skipped_path.pop(0)

            skipped_path.append(complete_path[-1])

            return skipped_path
        else:
            logger.debug(f"No Path found s{start}, g{goal}")
            return None

    def pathfind_with_nyduses(
        self,
        start: Tuple[float, float],
        goal: Tuple[float, float],
        grid: Optional[ndarray] = None,
        large: bool = False,
        smoothing: bool = False,
        sensitivity: int = 1,
    ) -> Optional[Tuple[List[List[Point2]], Optional[List[int]]]]:
        if grid is None:
            logger.warning("Using the default pyastar grid as no grid was provided.")
            grid = self.get_pyastar_grid()

        if start is not None and goal is not None:
            start = round(start[0]), round(start[1])
            start = self.find_eligible_point(start, grid, self.terrain_height, 10)
            goal = round(goal[0]), round(goal[1])
            goal = self.find_eligible_point(goal, grid, self.terrain_height, 10)
        else:
            logger.warning(PatherNoPointsException(start=start, goal=goal))
            return None

        # find_eligible_point didn't find any pathable nodes nearby
        if start is None or goal is None:
            return None

        nydus_units = self.map_data.bot.structures.of_type(
            [UnitTypeId.NYDUSNETWORK, UnitTypeId.NYDUSCANAL]
        ).ready
        nydus_positions = [nydus.position for nydus in nydus_units]

        paths = astar_path_with_nyduses(
            grid, start, goal, nydus_positions, large, smoothing
        )
        if paths is not None:
            returned_path = []
            nydus_tags = None
            if len(paths) == 1:
                path = list(map(Point2, paths[0]))
                skipped_path = path[0:-1:sensitivity]
                if skipped_path:
                    skipped_path.pop(0)
                skipped_path.append(path[-1])
                returned_path.append(skipped_path)
            else:
                first_path = list(map(Point2, paths[0]))
                first_skipped_path = first_path[0:-1:sensitivity]
                if first_skipped_path:
                    first_skipped_path.pop(0)
                first_skipped_path.append(first_path[-1])
                returned_path.append(first_skipped_path)

                enter_nydus_unit = nydus_units.filter(
                    lambda x: x.position.rounded == first_path[-1]
                ).first
                enter_nydus_tag = enter_nydus_unit.tag

                second_path = list(map(Point2, paths[1]))
                exit_nydus_unit = nydus_units.filter(
                    lambda x: x.position.rounded == second_path[0]
                ).first
                exit_nydus_tag = exit_nydus_unit.tag
                nydus_tags = [enter_nydus_tag, exit_nydus_tag]

                second_skipped_path = second_path[0:-1:sensitivity]
                second_skipped_path.append(second_path[-1])
                returned_path.append(second_skipped_path)

            return returned_path, nydus_tags
        else:
            logger.debug(f"No Path found s{start}, g{goal}")
            return None

    def add_cost(
        self,
        position: Tuple[float, float],
        radius: float,
        arr: ndarray,
        weight: float = 100,
        safe: bool = True,
        initial_default_weights: float = 0,
    ) -> ndarray:
        disk = tuple(draw_circle(position, radius, arr.shape))

        arr: ndarray = self._add_disk_to_grid(
            position, arr, disk, weight, safe, initial_default_weights
        )

        return arr

    def add_cost_to_multiple_grids(
        self,
        position: Tuple[float, float],
        radius: float,
        arrays: List[ndarray],
        weight: float = 100,
        safe: bool = True,
        initial_default_weights: float = 0,
    ) -> List[ndarray]:
        """
        Add the same cost to multiple grids, this is so the disk is only calculated once
        """
        disk = tuple(draw_circle(position, radius, arrays[0].shape))

        for i, arr in enumerate(arrays):
            arrays[i] = self._add_disk_to_grid(
                position, arrays[i], disk, weight, safe, initial_default_weights
            )

        return arrays

    @staticmethod
    def _add_disk_to_grid(
        position: Tuple[float, float],
        arr: ndarray,
        disk: Tuple,
        weight: float = 100,
        safe: bool = True,
        initial_default_weights: float = 0,
    ) -> ndarray:
        # if we don't touch any cell origins due to a small radius, add at least the cell
        # the given position is in
        if (
            len(disk[0]) == 0
            and 0 <= position[0] < arr.shape[0]
            and 0 <= position[1] < arr.shape[1]
        ):
            disk = (int(position[0]), int(position[1]))

        if initial_default_weights > 0:
            arr[disk] = np.where(arr[disk] == 1, initial_default_weights, arr[disk])

        arr[disk] += weight
        if safe and np.any(arr[disk] < 1):
            logger.warning(
                "You are attempting to set weights that are below 1. falling back to the minimum (1)"
            )
            arr[disk] = np.where(arr[disk] < 1, 1, arr[disk])

        return arr
