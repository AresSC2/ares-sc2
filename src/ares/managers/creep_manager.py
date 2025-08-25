import random
from typing import Any

import numpy as np
from cython_extensions import cy_distance_to, cy_distance_to_squared
from map_analyzer import MapData
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units
from scipy.ndimage import convolve

from ares.cache import property_cache_once_per_frame
from ares.consts import CREEP_TUMOR_TYPES, ManagerName, ManagerRequestType
from ares.managers.manager import Manager
from ares.managers.manager_mediator import IManagerMediator, ManagerMediator


class CreepManager(Manager, IManagerMediator):
    _creep_grid: np.ndarray
    _creep_tiles: tuple[np.ndarray, np.ndarray]
    EDGE_FILTER: np.ndarray = np.array([[-1, -1, -1], [-1, 8, -1], [-1, -1, -1]])

    def __init__(self, ai, config: dict, mediator: ManagerMediator) -> None:
        super().__init__(ai, config, mediator)
        self._creep_coverage: float = 0.0
        self._overlord_spotter_dict: dict[int:Point2] = dict()
        self._setup_overlord_spotter_dict: bool = False
        self.manager_requests_dict = {
            ManagerRequestType.FIND_NEARBY_CREEP_EDGE_POSITION: (
                lambda kwargs: self._find_nearby_creep_edge_position(**kwargs)
            ),
            ManagerRequestType.GET_CLOSEST_CREEP_TILE: (
                lambda kwargs: self._get_closest_creep_tile(**kwargs)
            ),
            ManagerRequestType.GET_CREEP_COVERAGE: lambda kwargs: self._creep_coverage,
            ManagerRequestType.GET_CREEP_EDGES: lambda kwargs: self.get_creep_edges,
            ManagerRequestType.GET_CREEP_GRID: lambda kwargs: self.get_creep_grid,
            ManagerRequestType.GET_CREEP_TILES: lambda kwargs: self.get_creep_tiles,
            ManagerRequestType.GET_NEXT_TUMOR_ON_PATH: (
                lambda kwargs: self._get_next_tumor_on_path(**kwargs)
            ),
            ManagerRequestType.GET_OVERLORD_CREEP_SPOTTER_POSTIONS: (
                lambda kwargs: self._get_overlord_creep_spotter_positions(**kwargs)
            ),
            ManagerRequestType.GET_RANDOM_CREEP_POSITION: (
                lambda kwargs: self._get_random_creep_position(**kwargs)
            ),
            ManagerRequestType.GET_TUMOR_INFLUENCE_LOWEST_COST_POSITION: (
                lambda kwargs: self._get_tumor_influence_lowest_cost_position(**kwargs)
            ),
        }

    def manager_request(
        self,
        receiver: ManagerName,
        request: ManagerRequestType,
        reason: str = None,
        **kwargs,
    ) -> Any:
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
        Optional[Union[BotMode, List[BotMode]]] :
            Either one of the ability dictionaries is being returned or a function that
            returns None was called from a different manager (please don't do that).

        """
        return self.manager_requests_dict[request](kwargs)

    @property_cache_once_per_frame
    def get_creep_edges(self) -> tuple[np.ndarray, np.ndarray]:
        creep_grid = self.get_creep_grid
        edges = convolve(creep_grid, self.EDGE_FILTER, mode="constant")

        # Get the pathable grid and create a filter for areas near unpathable terrain
        pathable_grid = self.ai.game_info.pathing_grid.data_numpy

        # Create a 3x3 kernel to check surrounding area
        kernel = np.ones((3, 3), dtype=np.uint8)

        # Convolve pathable grid - areas near unpathable terrain will have values < 9
        pathable_convolved = convolve(
            pathable_grid.astype(np.uint8), kernel, mode="constant", cval=1
        )

        # Only keep edges where all surrounding tiles are pathable (value == 9)
        valid_pathable_mask = pathable_convolved == 9

        # Combine edge detection with pathable mask
        valid_edges = (edges > 1) & valid_pathable_mask

        edge_y, edge_x = np.where(valid_edges)
        return edge_y, edge_x

    @property_cache_once_per_frame
    def get_creep_grid(self) -> np.ndarray:
        return self.ai.state.creep.data_numpy

    @property_cache_once_per_frame
    def get_creep_tiles(self) -> np.ndarray:
        positions = np.where(self.get_creep_grid == 1.0)
        return np.column_stack(positions)

    @property_cache_once_per_frame
    def existing_tumor_positions_or_order_targets(self) -> list[Point2]:
        own_structures_dict: dict[
            UnitTypeId, Units
        ] = self.manager_mediator.get_own_structures_dict
        positions: list[Point2] = [
            u.position
            for creep_tumor_type in CREEP_TUMOR_TYPES
            for u in own_structures_dict[creep_tumor_type]
        ]
        positions.extend(
            [
                u.order_target
                for u in self.manager_mediator.get_own_army_dict[UnitTypeId.QUEEN]
                if u.is_using_ability(AbilityId.BUILD_CREEPTUMOR)
            ]
        )
        return positions

    @property_cache_once_per_frame
    def get_tumor_influence_grid(self) -> np.ndarray:
        """Get a grid showing tumor influence (cost) across the map."""
        # Start with base cost grid from map data
        tumor_influence_grid: np.ndarray = (
            self.manager_mediator.get_cached_ground_grid.copy()
        )

        # Add cost around existing tumors
        for position in self.existing_tumor_positions_or_order_targets:
            # Add high cost around each tumor (discourages clustering)
            tumor_influence_grid = self.manager_mediator.get_map_data_object.add_cost(
                grid=tumor_influence_grid, position=position, weight=50.0, radius=5.0
            )

        return tumor_influence_grid

    async def update(self, iteration: int) -> None:
        # once every 5 seconds, calculate creep coverage
        if self.ai.state.game_loop % 112 == 0:
            # Get the creep and pathing grids
            creep_grid = self.get_creep_grid.T
            pathing_grid = self.manager_mediator.get_ground_grid

            # Create a mask of pathable terrain (where pathing_grid is not np.inf)
            pathable_mask = ~np.isinf(pathing_grid)

            # Count pathable tiles with creep and total pathable tiles
            pathable_with_creep = np.sum((creep_grid == 1) & pathable_mask)
            total_pathable_tiles = np.sum(pathable_mask)

            # Calculate coverage percentage
            self._creep_coverage = (
                (pathable_with_creep / total_pathable_tiles) * 100
                if total_pathable_tiles > 0
                else 0.0
            )

    def _get_closest_creep_tile(self, pos: Point2) -> Point2 | None:
        """Find the closest creep tile to the given position.

        Args:
            pos: A Point2 object representing the position to check

        Returns:
            Point2 object representing the closest creep tile coordinates
            or None if no creep tiles
        """
        # Get the array of creep tile coordinates
        tiles = self.get_creep_tiles

        if tiles is None or tiles.size == 0:
            return None

        # Calculate squared distances efficiently with NumPy broadcasting
        # Note: position is (x,y), but creep_tiles are stored as (y,x)
        squared_distances = (tiles[:, 0] - pos.y) ** 2 + (tiles[:, 1] - pos.x) ** 2

        # Find the index of the minimum distance
        min_index = np.argmin(squared_distances)

        # Return the closest point as Point2(x, y)
        # Convert from (y,x) format to (x,y) for Point2
        return Point2((float(tiles[min_index][1]), float(tiles[min_index][0])))

    def _get_next_tumor_on_path(
        self,
        grid: np.ndarray,
        from_pos: Point2,
        to_pos: Point2,
        max_distance: float = 999.9,
        min_distance: float = 0.0,
        min_separation: float = 5.0,
        find_alternative: bool = True,
    ) -> Point2 | None:
        """
        Determines the next tumor position on the path, using vectorized operations
        to find positions along the creep edge that maintain proper separation.

        Parameters:
            grid : np.ndarray
                A 2D array to path on.
            from_pos : Point2
                The starting position from which the path is evaluated.
            to_pos : Point2
                The target position on the grid where the path leads.
            max_distance : float, optional
                The maximum allowable distance from the `from_pos` to the
                next tumor position.
                Default is 999.9.
            min_distance: float, optional
                The minimum allowable distance from the `from_pos` to the
                next tumor position.
                Default is 0.0.
            min_separation: float, optional
                The minimum distance required between the new
                tumor and existing tumors/queen routes.
                Default is 3.0.
            find_alternative: bool, optional
                Find an alternative position if the closest position is
                too close to existing tumors
                Switch to False if possible to avoid unnecessary checks.
                Default is True.

        Returns:
            Point2 or None
                Returns the next suitable tumor position on the grid if a valid
                position is found within the specified conditions.
                Returns None if no valid position exists.
        """

        if path := self.manager_mediator.find_raw_path(
            start=from_pos, target=to_pos, grid=grid, sensitivity=1
        ):
            for point in path:
                if not self.ai.has_creep(point) and (
                    creep_pos := self._get_closest_creep_tile(pos=point)
                ):
                    distance: float = cy_distance_to(from_pos, creep_pos)

                    # Check if position is within desired distance range
                    if (
                        max_distance > distance > min_distance
                        and self._valid_creep_placement(creep_pos, visible_check=False)
                    ):
                        if not find_alternative:
                            return creep_pos

                        # Check if position is far enough from existing tumors
                        too_close = False
                        for pos in self.existing_tumor_positions_or_order_targets:
                            if cy_distance_to(pos, creep_pos) < min_separation:
                                too_close = True
                                break

                        if not too_close:
                            # If this position is good, return it immediately
                            return creep_pos
                        else:
                            # find a nearby alternative on the creep edge
                            alternative_pos = self._find_nearby_creep_edge_position(
                                creep_pos, min_separation
                            )
                            if alternative_pos:
                                return alternative_pos

                        return None

        return None

    def _find_nearby_creep_edge_position(
        self,
        position: Point2,
        search_radius: float = 15.0,
        closest_valid: bool = True,
        spread_dist: float = 3.0,
    ) -> Point2 | None:
        """Find the closest creep edge position near a given position using convolution.

        Parameters
        ----------
        position : Point2
            The center position to search around
        search_radius : int, optional
            Radius in tiles to search around the position, by default 15
        closest_valid: bool, optional
            Find the closest valid creep edge position?
            Default is True.


        Returns
        -------
        Point2 | None
            The closest edge position, or None if no edges found
        """
        edge_y, edge_x = self.get_creep_edges

        if len(edge_x) == 0:
            return None

        # Calculate distances from the search position
        distances = np.sqrt((edge_x - position.x) ** 2 + (edge_y - position.y) ** 2)

        # Filter to only edges within search radius
        within_radius = distances <= search_radius
        if not np.any(within_radius):
            return None

        valid_edges = []

        for i, (x, y) in enumerate(zip(edge_x[within_radius], edge_y[within_radius])):
            edge_pos = Point2((float(x), float(y)))
            if not self._valid_creep_placement(edge_pos):
                continue

            # Check if far enough from all existing tumors
            if all(
                cy_distance_to(edge_pos, tumor_pos) >= spread_dist
                for tumor_pos in self.existing_tumor_positions_or_order_targets
            ):
                valid_edges.append((i, edge_pos))

        if not valid_edges:
            return None

        # Find the closest valid edge
        if closest_valid:
            idx, pos = min(
                valid_edges, key=lambda pos: cy_distance_to_squared(position, pos[1])
            )
        else:
            idx, pos = max(
                valid_edges, key=lambda pos: cy_distance_to_squared(position, pos[1])
            )

        return pos

    def _get_overlord_creep_spotter_positions(
        self, overlords: Units | list[Unit], target_pos: Point2
    ) -> dict[int, Point2]:
        """Find optimal positions for overlords to provide vision for creep spread.

        This function finds the edge of creep and distributes
        overlord positions evenly around it.

        Parameters:
            overlords : Units | list[Unit]
                The overlords that will be positioned for creep vision

        Returns:
            dict[int: Point2]
                Dictionary mapping overlord tag to position where it should move
        """
        if not overlords:
            return {}

        edge_y, edge_x = self.get_creep_edges

        if len(edge_x) == 0:
            return {}

        # Calculate distances in numpy
        distances = np.sqrt((edge_x - target_pos.x) ** 2 + (edge_y - target_pos.y) ** 2)

        num_to_keep = len(edge_x) - 1
        closest_indices = np.argpartition(distances, num_to_keep)[:num_to_keep]

        # Filter arrays to only closest edges
        edge_x_filtered = edge_x[closest_indices]
        edge_y_filtered = edge_y[closest_indices]
        distances_filtered = distances[closest_indices]

        # Sort by distance (closest first)
        sort_indices = np.argsort(distances_filtered)
        edge_x_sorted = edge_x_filtered[sort_indices]
        edge_y_sorted = edge_y_filtered[sort_indices]

        # Now convert to Point2 objects
        edge_points = [
            Point2((float(x), float(y))) for x, y in zip(edge_x_sorted, edge_y_sorted)
        ]

        # Select positions with minimum separation
        target_positions = []
        min_separation = 18.0  # Minimum distance between overlord positions

        for edge_point in edge_points:
            # Check if this point is far enough from already selected positions
            if not any(
                cy_distance_to(edge_point, existing) < min_separation
                for existing in target_positions
            ):
                target_positions.append(edge_point)

                # Stop when we have enough positions
                if len(target_positions) >= len(overlords):
                    break

        # Assign closest overlord to each position to minimize movement
        result = {}
        available_overlords = list(overlords)

        for position in target_positions:
            if not available_overlords:
                break

            # Find closest available overlord
            closest_overlord = min(
                available_overlords,
                key=lambda o: cy_distance_to_squared(position, o.position),
            )
            final_position = position
            # keep the overlord where it is if close
            if (
                not closest_overlord.is_moving
                and cy_distance_to_squared(closest_overlord.position, position) < 81.0
            ):
                final_position = closest_overlord.position

            # Ensure within map bounds
            map_width, map_height = self.ai.game_info.map_size
            final_position = Point2(
                (
                    max(1, min(map_width - 1, final_position.x)),
                    max(1, min(map_height - 1, final_position.y)),
                )
            )

            result[closest_overlord.tag] = final_position
            available_overlords.remove(closest_overlord)

        return result

    def _get_tumor_influence_lowest_cost_position(
        self, position: Point2
    ) -> Point2 | None:
        """
        Determines the lowest cost position influenced by the tumor through a request
        to the creep manager.

        This method sends a request to the creep manager to retrieve the position
        with the lowest cost under tumor influence. The operation is executed
        via the manager_request function.

        Parameters:
            position : Point2
                Tumor position.

        Returns:
            Point2:
                Furthest placement with lowest cost under tumor influence.

        """
        map_data: MapData = self.manager_mediator.get_map_data_object
        lowest_points = map_data.lowest_cost_points_array(
            from_pos=position, radius=9, grid=self.get_tumor_influence_grid
        )

        # Sort by distance (closest first) to minimize tumor movement
        candidates = sorted(
            lowest_points,
            key=lambda spot: cy_distance_to_squared(spot, position),
        )

        # Test candidates starting from furthest (lowest cost areas)
        for candidate in reversed(candidates):
            candidate_pos = Point2(candidate)

            # Quick distance check - must be 3+ tiles from tumor
            if cy_distance_to(candidate_pos, position) < 3.0:
                continue

            # Additional validation for creep placement
            if self._valid_creep_placement(candidate_pos):
                return candidate_pos

        return None

    def _position_blocks_expansion(self, position: Point2) -> bool:
        """Will the creep tumor block expansion"""
        blocks_expansion: bool = False
        for expansion in self.ai.expansion_locations_list:
            if cy_distance_to_squared(position, expansion) < 25.0:
                blocks_expansion = True
                break
        return blocks_expansion

    def _valid_creep_placement(
        self, position: Point2, visible_check: bool = True
    ) -> bool:
        origin_x: int = int(round(position.x))
        origin_y: int = int(round(position.y))

        # Fix 2: Add bounds checking before accessing arrays
        map_width, map_height = self.ai.game_info.map_size
        if (
            origin_x < 0
            or origin_x >= map_width
            or origin_y < 0
            or origin_y >= map_height
        ):
            return False

        visible: bool = False
        if not visible_check or (visible_check and self.ai.is_visible(position)):
            visible = True

        return (
            visible
            and self.ai.has_creep(position)
            and not self._position_blocks_expansion(position)
            and self.manager_mediator.is_position_safe(
                grid=self.manager_mediator.get_ground_grid, position=position
            )
            and self.ai.in_placement_grid(position)
        )

    def _get_random_creep_position(
        self, position: Point2, max_attempts: int = 20
    ) -> Point2 | None:
        """Find a random valid creep position within tumor range.

        Parameters:
            position : Point2
                The position to search from.
            max_attempts : int
                Maximum attempts to find a valid position.

        Returns:
            Point2 | None
                Random creep position.
        """

        for _ in range(max_attempts):
            # Generate random angle and distance
            angle = random.uniform(0, 2 * np.pi)
            distance = random.uniform(
                6.0, 9.0
            )  # Random distance between min and max range

            candidate_pos = Point2(
                (
                    position.x + distance * np.cos(angle),
                    position.y + distance * np.sin(angle),
                )
            )

            # Check bounds
            if (
                candidate_pos.x < 1
                or candidate_pos.x >= self.ai.game_info.map_size[0] - 1
                or candidate_pos.y < 1
                or candidate_pos.y >= self.ai.game_info.map_size[1] - 1
            ):
                continue

            if self._valid_creep_placement(candidate_pos):
                return candidate_pos

        return None
