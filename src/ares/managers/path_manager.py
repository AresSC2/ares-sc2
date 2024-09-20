"""Handle pathing and grid information.

"""
from typing import TYPE_CHECKING, Any, Dict, List, Union

import numpy as np
from cython_extensions import cy_distance_to_squared, cy_point_below_value
from map_analyzer import MapData
from sc2.ids.effect_id import EffectId
from sc2.ids.unit_typeid import UnitTypeId as UnitID
from sc2.position import Point2
from sc2.unit import Unit
from scipy import spatial
from scipy.spatial import KDTree

from ares.consts import (
    ACTIVE_GRID,
    AIR,
    AIR_AVOIDANCE,
    AIR_COST,
    AIR_RANGE,
    AIR_VS_GROUND,
    AIR_VS_GROUND_DEFAULT,
    BLINDING_CLOUD,
    CHANGELING_TYPES,
    CORROSIVE_BILE,
    COST,
    COST_MULTIPLIER,
    DANGER_THRESHOLD,
    DANGER_TILES,
    DEBUG,
    DEBUG_OPTIONS,
    EFFECTS,
    EFFECTS_RANGE_BUFFER,
    GROUND,
    GROUND_AVOIDANCE,
    GROUND_COST,
    GROUND_RANGE,
    GROUND_TO_AIR,
    KD8_CHARGE,
    LIBERATOR_ZONE,
    LURKER_SPINE,
    NUKE,
    ORACLE,
    PARASITIC_BOMB,
    PATHING,
    PATHING_GRID,
    RANGE,
    RANGE_BUFFER,
    SHOW_PATHING_COST,
    STORM,
    TOWNHALL_TYPES,
    UNITS,
    ManagerName,
    ManagerRequestType,
)
from ares.dicts.weight_costs import WEIGHT_COSTS
from ares.managers.manager import Manager
from ares.managers.manager_mediator import IManagerMediator, ManagerMediator

if TYPE_CHECKING:
    from ares import AresBot


class PathManager(Manager, IManagerMediator):
    """Manager for handling paths.

    All unit pathing should be done here
    This also exposes SC2MapAnalyzer api_reference through `self.map_data`

    """

    BILE_DURATION: int = 50
    REACT_TO_BILES_ON_FRAME: int = 16
    FORCEFIELD: str = "FORCEFIELD"
    NUKE_DURATION: int = 320
    REACT_TO_NUKES_ON_FRAME: int = 250

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
        super().__init__(ai, config, mediator)
        self.manager_requests_dict = {
            ManagerRequestType.GET_AIR_AVOIDANCE_GRID: lambda kwargs: (
                self.air_avoidance_grid
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
            ManagerRequestType.GET_FORCEFIELD_POSITIONS: lambda kwargs: (
                self.forcefield_positions
            ),
            ManagerRequestType.GET_AIR_GRID: lambda kwargs: self.air_grid,
            ManagerRequestType.GET_AIR_VS_GROUND_GRID: lambda kwargs: (
                self.air_vs_ground_grid
            ),
            ManagerRequestType.GET_CACHED_GROUND_GRID: lambda kwargs: (
                self._cached_clean_ground_grid
            ),
            ManagerRequestType.GET_CLOSEST_SAFE_SPOT: lambda kwargs: (
                self.find_closest_safe_spot(**kwargs)
            ),
            ManagerRequestType.GET_GROUND_AVOIDANCE_GRID: lambda kwargs: (
                self.ground_avoidance_grid
            ),
            ManagerRequestType.GET_GROUND_TO_AIR_GRID: lambda kwargs: (
                self.ground_to_air_grid
            ),
            ManagerRequestType.GET_CLIMBER_GRID: lambda kwargs: self.climber_grid,
            ManagerRequestType.GET_GROUND_GRID: lambda kwargs: self.ground_grid,
            ManagerRequestType.GET_MAP_DATA: lambda kwargs: self.map_data,
            ManagerRequestType.GET_PRIORITY_GROUND_AVOIDANCE_GRID: lambda kwargs: (
                self.priority_ground_avoidance_grid
            ),
            ManagerRequestType.GET_WHOLE_MAP_ARRAY: lambda kwargs: self.whole_map,
            ManagerRequestType.GET_WHOLE_MAP_TREE: lambda kwargs: self.whole_map_tree,
            ManagerRequestType.PATH_NEXT_POINT: lambda kwargs: (
                self.find_path_next_point(**kwargs)
            ),
        }

        self.debug: bool = self.config[DEBUG]
        self.map_data: MapData = MapData(ai, arcade=self.ai.arcade_mode)

        self.air_grid: np.ndarray = self.map_data.get_clean_air_grid()
        # grid where ground pathable tiles have influence so flyers avoid
        self.air_vs_ground_grid: np.ndarray = self.map_data.get_air_vs_ground_grid(
            default_weight=AIR_VS_GROUND_DEFAULT
        )
        self.climber_grid: np.ndarray = self.map_data.get_climber_grid()
        self.ground_grid: np.ndarray = self.map_data.get_pyastar_grid()
        # tiles without creep are listed as unpathable
        self.creep_ground_grid: np.ndarray = self.map_data.get_pyastar_grid()
        # this is like the air grid above,
        # but only add influence from enemy ground
        self.ground_to_air_grid: np.ndarray = self.air_grid.copy()

        self._cached_clean_air_grid: np.ndarray = self.air_grid.copy()
        self._cached_clean_air_vs_ground_grid: np.ndarray = (
            self.air_vs_ground_grid.copy()
        )

        self._cached_clean_ground_grid: np.ndarray = self.ground_grid.copy()
        self._cached_climber_grid: np.ndarray = self.climber_grid.copy()
        # avoidance grids will contain influence for things our units should avoid
        self.air_avoidance_grid: np.ndarray = self._cached_clean_air_grid.copy()
        self.ground_avoidance_grid: np.ndarray = self._cached_clean_ground_grid.copy()
        # certain things ground units should always avoid
        self.priority_ground_avoidance_grid: np.ndarray = (
            self._cached_clean_ground_grid.copy()
        )

        self.whole_map: List[List[int]] = [
            [x, y]
            for x in range(self.ai.game_info.map_size[0])
            for y in range(self.ai.game_info.map_size[1])
        ]
        self.whole_map_tree: KDTree = KDTree(self.whole_map)
        # vague attempt at not recalculating np.argwhere for danger tiles
        self.calculated_danger_tiles: List[Dict[str, Union[np.ndarray, int]]] = []
        self.forcefield_positions: List[Point2] = []
        # biles / nukes
        self.delayed_effects: Dict[int, int] = {}

        # track biles, since they disappear from the observation right before they land
        # key is position, value is the frame the bile was first seen (50 frames total)
        self.biles_dict: Dict[Point2, int] = dict()
        self.storms_dict: Dict[Point2, int] = dict()

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

        """
        return self.manager_requests_dict[request](kwargs)

    async def update(self, iteration: int) -> None:
        """Keep track of everything.

        Parameters
        ----------
        iteration :
            The game iteration.

        Returns
        -------

        """
        self.forcefield_positions = []
        self._add_effects()

        # nukes / biles
        self._update_delayed_effects()

        if iteration % 4 == 0:
            self.calculated_danger_tiles = []

        for unit in self.ai.enemy_units:
            if unit.type_id not in CHANGELING_TYPES:
                self.add_unit_influence(unit)

        # update creep grid
        self.creep_ground_grid = self.ground_grid.copy()
        self.creep_ground_grid[np.where(self.ai.state.creep.data_numpy.T != 1)] = np.inf

        if self.debug and self.config[DEBUG_OPTIONS][SHOW_PATHING_COST]:
            if self.config[DEBUG_OPTIONS][ACTIVE_GRID] == AIR:
                self.map_data.draw_influence_in_game(self.air_grid, lower_threshold=1)
            elif self.config[DEBUG_OPTIONS][ACTIVE_GRID] == AIR_VS_GROUND:
                self.map_data.draw_influence_in_game(
                    self.air_vs_ground_grid, lower_threshold=40
                )
            elif self.config[DEBUG_OPTIONS][ACTIVE_GRID] == GROUND:
                self.map_data.draw_influence_in_game(
                    self.ground_grid, lower_threshold=1
                )
            elif self.config[DEBUG_OPTIONS][ACTIVE_GRID] == GROUND_AVOIDANCE:
                self.map_data.draw_influence_in_game(
                    self.ground_avoidance_grid, lower_threshold=1
                )
            elif self.config[DEBUG_OPTIONS][ACTIVE_GRID] == AIR_AVOIDANCE:
                self.map_data.draw_influence_in_game(
                    self.air_avoidance_grid, lower_threshold=1
                )
            elif self.config[DEBUG_OPTIONS][ACTIVE_GRID] == GROUND_TO_AIR:
                self.map_data.draw_influence_in_game(
                    self.ground_to_air_grid, lower_threshold=1
                )

    def add_cost(
        self,
        pos: Point2,
        weight: float,
        unit_range: float,
        grid: np.ndarray,
        initial_default_weights: int = 0,
    ) -> np.ndarray:
        """Add values to a grid.

        Costs can also be considered "influence", mostly used to add enemies to a grid.

        Parameters
        ----------
        pos :
            Where the cause of the increased cost is located.
        weight :
            How much the cost should change by.
        unit_range :
            Radius of a circle centered at pos that contains all points that the cost
            should be added to.
        grid :
            Which pathing grid to increase the costs of.
        initial_default_weights :
            Default value of the grid being added to.

        Returns
        -------

        """

        grid = self.map_data.add_cost(
            position=(int(pos.x), int(pos.y)),
            radius=unit_range,
            grid=grid,
            weight=int(weight) * self.config[PATHING][COST_MULTIPLIER],
            initial_default_weights=initial_default_weights,
        )
        return grid

    def add_cost_to_multiple_grids(
        self,
        pos: Point2,
        weight: float,
        unit_range: float,
        grids: List[np.ndarray],
        initial_default_weights: int = 0,
    ) -> List[np.ndarray]:
        """Add values to multiple grids at once.

        Costs can also be considered "influence", mostly used to add enemies to a grid.

        Parameters
        ----------
        pos :
            Where the cause of the increased cost is located.
        weight :
            How much the cost should change by.
        unit_range :
            Radius of a circle centered at pos that contains all points that the cost
            should be added to.
        grids :
            Which pathing grids to increase the costs of.
        initial_default_weights :
            Default value of the grid being added to.

        Returns
        -------

        """

        return self.map_data.add_cost_to_multiple_grids(
            position=(int(pos.x), int(pos.y)),
            radius=unit_range,
            grids=grids,
            weight=int(weight) * self.config[PATHING][COST_MULTIPLIER],
            initial_default_weights=initial_default_weights,
        )

    def find_closest_safe_spot(
        self, from_pos: Point2, grid: np.ndarray, radius: int = 7
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
        danger_distance: int = 20,
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
        bool:
            True if the position is considered safe, False otherwise.

        """
        return cy_point_below_value(grid, position.rounded, weight_safety_limit)

    def reset_grids(self, iteration: int) -> None:
        """Get fresh grids so that the influence can be updated.

        Parameters
        ----------
        iteration :
            The current game iteration.

        Returns
        -------

        """
        self.air_grid = self._cached_clean_air_grid.copy()
        self.air_vs_ground_grid = self._cached_clean_air_vs_ground_grid.copy()
        self.climber_grid = self._cached_climber_grid.copy()
        self.ground_grid = self._cached_clean_ground_grid.copy()
        self.air_avoidance_grid = self._cached_clean_air_grid.copy()
        self.ground_avoidance_grid = self._cached_clean_ground_grid.copy()
        self.priority_ground_avoidance_grid = self._cached_clean_ground_grid.copy()
        self.ground_to_air_grid = self._cached_clean_air_grid.copy()

        # Refresh the cached ground grid every 8 steps, because things like structures/
        # minerals / rocks will change throughout the game
        # TODO: Detect changes in structures / rocks / min field, then update?
        #   Only if this is faster then updating the grid!
        if iteration % 8 == 0:
            self._cached_clean_ground_grid = self.map_data.get_pyastar_grid()
            self._cached_climber_grid = self.map_data.get_climber_grid()

    def add_unit_influence(self, enemy: Unit) -> None:
        """Add influence to the relevant grid.

        Called from _prepare_units.
        Work in progress.

        Parameters
        ----------
        enemy :
            The enemy unit to add the influence of.

        Returns
        -------

        """

        if not enemy.is_ready and not enemy.is_cloaked and not enemy.is_burrowed:
            return
        self._add_unit_influence(enemy)

    def add_structure_influence(self, enemy: Unit) -> None:
        """Add structure influence to the relevant grid.

        Called from _prepare_units.

        Parameters
        ----------
        enemy :
            The enemy structure to add the influence of.

        Returns
        -------

        """
        # these will expire out of our vision, don't add to grid
        if enemy.type_id == UnitID.AUTOTURRET and enemy.is_snapshot:
            return
        if enemy.is_ready:
            self._add_structure_influence(enemy)

    def _add_effects(self) -> None:
        """Add effects influence to map.

        Returns
        -------

        """
        effect_values: Dict = self.config[PATHING][EFFECTS]

        for effect in self.ai.state.effects:
            # blinding cloud
            if effect.id == EffectId.BLINDINGCLOUDCP:
                (
                    self.climber_grid,
                    self.ground_grid,
                    self.ground_avoidance_grid,
                ) = self.add_cost_to_multiple_grids(
                    Point2.center(effect.positions),
                    effect_values[BLINDING_CLOUD][COST],
                    effect_values[BLINDING_CLOUD][RANGE]
                    + self.config[PATHING][EFFECTS_RANGE_BUFFER],
                    [self.climber_grid, self.ground_grid, self.ground_avoidance_grid],
                )
            elif effect.id == "KD8CHARGE":
                (
                    self.climber_grid,
                    self.ground_grid,
                    # self.ground_avoidance_grid,
                ) = self.add_cost_to_multiple_grids(
                    Point2.center(effect.positions),
                    effect_values[KD8_CHARGE][COST],
                    effect_values[KD8_CHARGE][RANGE]
                    + self.config[PATHING][EFFECTS_RANGE_BUFFER],
                    [self.climber_grid, self.ground_grid],
                )
            # liberator siege
            elif effect.id in {
                EffectId.LIBERATORTARGETMORPHDELAYPERSISTENT,
                EffectId.LIBERATORTARGETMORPHPERSISTENT,
            }:
                (
                    self.climber_grid,
                    self.ground_grid,
                    # self.ground_avoidance_grid,
                ) = self.add_cost_to_multiple_grids(
                    Point2.center(effect.positions),
                    effect_values[LIBERATOR_ZONE][COST],
                    effect_values[LIBERATOR_ZONE][RANGE]
                    + self.config[PATHING][EFFECTS_RANGE_BUFFER],
                    [self.climber_grid, self.ground_grid],
                )
            # lurker spines
            elif effect.id == EffectId.LURKERMP:
                for pos in effect.positions:
                    (
                        self.climber_grid,
                        self.ground_grid,
                        self.ground_avoidance_grid,
                    ) = self.add_cost_to_multiple_grids(
                        pos,
                        effect_values[LURKER_SPINE][COST],
                        effect_values[LURKER_SPINE][RANGE]
                        + self.config[PATHING][EFFECTS_RANGE_BUFFER],
                        [
                            self.climber_grid,
                            self.ground_grid,
                            self.ground_avoidance_grid,
                        ],
                    )
            # nukes
            elif effect.id == EffectId.NUKEPERSISTENT:
                self._add_delayed_effect(
                    position=Point2.center(effect.positions),
                    effect_dict=self.storms_dict,
                )
            # storms
            elif effect.id == EffectId.PSISTORMPERSISTENT:
                (
                    self.air_grid,
                    self.air_vs_ground_grid,
                    self.climber_grid,
                    self.ground_grid,
                    self.air_avoidance_grid,
                    self.ground_avoidance_grid,
                    self.priority_ground_avoidance_grid,
                ) = self.add_cost_to_multiple_grids(
                    Point2.center(effect.positions),
                    effect_values[STORM][COST],
                    effect_values[STORM][RANGE]
                    + self.config[PATHING][EFFECTS_RANGE_BUFFER],
                    [
                        self.air_grid,
                        self.air_vs_ground_grid,
                        self.climber_grid,
                        self.ground_grid,
                        self.air_avoidance_grid,
                        self.ground_avoidance_grid,
                        self.priority_ground_avoidance_grid,
                    ],
                )
            # corrosive bile
            elif effect.id == EffectId.RAVAGERCORROSIVEBILECP:
                self._add_delayed_effect(
                    position=Point2.center(effect.positions),
                    effect_dict=self.biles_dict,
                )

            # forcefields (currently just keeping track of them)
            elif effect.id == self.FORCEFIELD:
                # forcefields only have 1 position but it's still a set
                self.forcefield_positions.append(effect.positions.pop())

        for position in self.ai.enemy_parasitic_bomb_positions:
            (
                self.air_grid,
                self.air_vs_ground_grid,
                self.air_avoidance_grid,
                self.ground_to_air_grid,
            ) = self.add_cost_to_multiple_grids(
                position,
                effect_values[PARASITIC_BOMB][COST],
                effect_values[PARASITIC_BOMB][RANGE]
                + self.config[PATHING][EFFECTS_RANGE_BUFFER],
                [
                    self.air_grid,
                    self.air_vs_ground_grid,
                    self.air_avoidance_grid,
                    self.ground_to_air_grid,
                ],
            )

    def _add_structure_influence(self, structure: Unit) -> None:
        """Add structure influence to map.

        Parameters
        ----------
        structure :
            The structure to add the influence of.

        Returns
        -------

        """
        if structure.type_id == UnitID.PHOTONCANNON:
            (
                self.air_grid,
                self.air_vs_ground_grid,
                self.climber_grid,
                self.ground_grid,
                self.ground_to_air_grid,
            ) = self.add_cost_to_multiple_grids(
                structure.position,
                22,
                7 + self.config[PATHING][RANGE_BUFFER],
                [
                    self.air_grid,
                    self.air_vs_ground_grid,
                    self.climber_grid,
                    self.ground_grid,
                    self.ground_to_air_grid,
                ],
            )
        elif structure.type_id == UnitID.MISSILETURRET:
            s_range: int = 8 if self.ai.time > 540 else 7
            (
                self.air_grid,
                self.air_vs_ground_grid,
                self.ground_to_air_grid,
            ) = self.add_cost_to_multiple_grids(
                structure.position,
                39,
                s_range + self.config[PATHING][RANGE_BUFFER],
                [self.air_grid, self.air_vs_ground_grid, self.ground_to_air_grid],
            )
        elif structure.type_id == UnitID.SPORECRAWLER:
            # 48 vs biological units, 24 otherwise
            (
                self.air_grid,
                self.air_vs_ground_grid,
                self.ground_to_air_grid,
            ) = self.add_cost_to_multiple_grids(
                structure.position,
                39,
                7 + self.config[PATHING][RANGE_BUFFER],
                [self.air_grid, self.air_vs_ground_grid, self.ground_to_air_grid],
            )
        elif structure.type_id == UnitID.BUNKER:
            if self.ai.enemy_structures.filter(
                lambda g: g.type_id in TOWNHALL_TYPES
                and cy_distance_to_squared(g.position, structure.position) < 81.0  # 9.0
            ):
                return
            # add range of marine + 1
            (
                self.air_grid,
                self.air_vs_ground_grid,
                self.climber_grid,
                self.ground_grid,
                self.ground_to_air_grid,
            ) = self.add_cost_to_multiple_grids(
                structure.position,
                22,
                6 + self.config[PATHING][RANGE_BUFFER],
                [
                    self.air_grid,
                    self.air_vs_ground_grid,
                    self.climber_grid,
                    self.ground_grid,
                    self.ground_to_air_grid,
                ],
            )
        elif structure.type_id == UnitID.PLANETARYFORTRESS:
            s_range: int = 7 if self.ai.time > 400 else 6
            (self.climber_grid, self.ground_grid,) = self.add_cost_to_multiple_grids(
                structure.position,
                28,
                s_range + self.config[PATHING][RANGE_BUFFER],
                [self.climber_grid, self.ground_grid],
            )
        elif structure.type_id == UnitID.AUTOTURRET:
            self._add_cost_to_all_grids(structure, WEIGHT_COSTS[UnitID.AUTOTURRET])

    def _add_unit_influence(self, unit: Unit) -> None:
        """Add unit influence to maps.

        Parameters
        ----------
        unit :
            The unit to add the influence of.

        Returns
        -------

        """
        if unit.type_id in WEIGHT_COSTS:
            weight_values = WEIGHT_COSTS[unit.type_id]
            self._add_cost_to_all_grids(unit, weight_values)
            if not unit.is_flying:
                self.ground_to_air_grid = self.map_data.add_cost(
                    unit.position,
                    weight_values[AIR_RANGE] + self.config[PATHING][RANGE_BUFFER],
                    self.ground_to_air_grid,
                    weight_values[AIR_COST],
                )
        elif unit.type_id == UnitID.DISRUPTORPHASED:
            (
                self.climber_grid,
                self.ground_avoidance_grid,
                self.ground_grid,
                self.priority_ground_avoidance_grid,
            ) = self.add_cost_to_multiple_grids(
                pos=unit.position,
                weight=1000,
                unit_range=8 + self.config[PATHING][EFFECTS_RANGE_BUFFER],
                grids=[
                    self.climber_grid,
                    self.ground_avoidance_grid,
                    self.ground_grid,
                    self.priority_ground_avoidance_grid,
                ],
            )
        elif unit.type_id == UnitID.BANELING:
            (
                self.climber_grid,
                self.ground_avoidance_grid,
                self.ground_grid,
                self.priority_ground_avoidance_grid,
            ) = self.add_cost_to_multiple_grids(
                pos=unit.position,
                weight=WEIGHT_COSTS[UnitID.BANELING][GROUND_COST],
                unit_range=WEIGHT_COSTS[UnitID.BANELING][GROUND_RANGE],
                grids=[
                    self.climber_grid,
                    self.ground_avoidance_grid,
                    self.ground_grid,
                    self.priority_ground_avoidance_grid,
                ],
            )
        # add the potential of a fungal growth
        elif unit.type_id == UnitID.INFESTOR and unit.energy >= 75:
            weight_values: dict = WEIGHT_COSTS[UnitID.INFESTOR]
            self._add_cost_to_all_grids(unit, WEIGHT_COSTS[UnitID.INFESTOR])
            self.ground_to_air_grid = self.map_data.add_cost(
                unit.position,
                weight_values[AIR_RANGE] + self.config[PATHING][RANGE_BUFFER],
                self.ground_to_air_grid,
                weight_values[AIR_COST],
            )
        elif unit.type_id == UnitID.ORACLE and unit.energy >= 25:
            self.climber_grid, self.ground_grid = self.add_cost_to_multiple_grids(
                unit.position,
                self.config[PATHING][UNITS][ORACLE][GROUND_COST],
                self.config[PATHING][UNITS][ORACLE][GROUND_RANGE]
                + self.config[PATHING][RANGE_BUFFER],
                [self.climber_grid, self.ground_grid],
            )
        # melee units
        elif unit.ground_range < 2:
            self.climber_grid, self.ground_grid = self.add_cost_to_multiple_grids(
                unit.position,
                unit.ground_dps,
                self.config[PATHING][RANGE_BUFFER],
                [self.climber_grid, self.ground_grid],
            )
        elif unit.can_attack_air:
            self.air_grid, self.air_vs_ground_grid = self.add_cost_to_multiple_grids(
                unit.position,
                unit.air_dps,
                unit.air_range + self.config[PATHING][RANGE_BUFFER],
                [self.air_grid, self.air_vs_ground_grid],
            )
            if not unit.is_flying:
                self.map_data.add_cost(
                    unit.position,
                    unit.air_range + self.config[PATHING][RANGE_BUFFER],
                    self.ground_to_air_grid,
                    unit.air_dps,
                )
        elif unit.can_attack_ground:
            self.climber_grid, self.ground_grid = self.add_cost_to_multiple_grids(
                unit.position,
                unit.ground_dps,
                unit.ground_range + self.config[PATHING][RANGE_BUFFER],
                [self.climber_grid, self.ground_grid],
            )

    def _add_cost_to_all_grids(self, unit: Unit, weight_values: Dict) -> None:
        """Add cost to all grids.

        TODO: Could perhaps be renamed as misleading name, cost is added to the main
            grids but not all

        Parameters
        ----------
        unit :
            Unit to add the costs of.
        weight_values :
            Dictionary containing the weights of units.

        Returns
        -------

        """
        if unit.type_id == UnitID.AUTOTURRET:
            (
                self.air_grid,
                self.air_vs_ground_grid,
                self.climber_grid,
                self.ground_grid,
                self.ground_avoidance_grid,
                self.air_avoidance_grid,
                self.ground_to_air_grid,
            ) = self.add_cost_to_multiple_grids(
                unit.position,
                weight_values[AIR_COST],
                weight_values[AIR_RANGE] + self.config[PATHING][RANGE_BUFFER],
                [
                    self.air_grid,
                    self.air_vs_ground_grid,
                    self.climber_grid,
                    self.ground_grid,
                    self.ground_avoidance_grid,
                    self.air_avoidance_grid,
                    self.ground_to_air_grid,
                ],
            )

        # values are identical for air and ground, add costs to all grids at same time
        elif (
            weight_values[AIR_COST] == weight_values[GROUND_COST]
            and weight_values[AIR_RANGE] == weight_values[GROUND_RANGE]
        ):
            (
                self.air_grid,
                self.air_vs_ground_grid,
                self.climber_grid,
                self.ground_grid,
            ) = self.add_cost_to_multiple_grids(
                unit.position,
                weight_values[AIR_COST],
                weight_values[AIR_RANGE] + self.config[PATHING][RANGE_BUFFER],
                [
                    self.air_grid,
                    self.air_vs_ground_grid,
                    self.climber_grid,
                    self.ground_grid,
                ],
            )
        # ground values are different, so add cost separately
        else:
            if weight_values[AIR_RANGE] > 0:
                (
                    self.air_grid,
                    self.air_vs_ground_grid,
                ) = self.add_cost_to_multiple_grids(
                    unit.position,
                    weight_values[AIR_COST],
                    weight_values[AIR_RANGE] + self.config[PATHING][RANGE_BUFFER],
                    [self.air_grid, self.air_vs_ground_grid],
                )
            if weight_values[GROUND_RANGE] > 0:
                (
                    self.climber_grid,
                    self.ground_grid,
                ) = self.add_cost_to_multiple_grids(
                    unit.position,
                    weight_values[GROUND_COST],
                    weight_values[GROUND_RANGE] + self.config[PATHING][RANGE_BUFFER],
                    [self.climber_grid, self.ground_grid],
                )

    def _add_delayed_effect(
        self,
        position: Point2,
        effect_dict: Dict,
    ) -> None:
        """Add an effect that we know exists but is not in the game observation.

        Parameters
        ----------
        position :
            Where to add the effect.
        effect_dict :
            Currently tracked effects.

        Returns
        -------

        """
        # no record of this yet
        if position not in effect_dict:
            effect_dict[position] = self.ai.state.game_loop

    def _clear_delayed_effects(self, effect_dict: Dict, effect_duration: int) -> None:
        """Remove delayed effects when they've expired.

        Parameters
        ----------
        effect_dict :
            Currently tracked effects.
        effect_duration :
            How long the effect lasts.

        Returns
        -------

        """
        current_frame: int = self.ai.state.game_loop
        keys_to_remove: List[Point2] = []

        for position, frame_commenced in effect_dict.items():
            if current_frame - frame_commenced > effect_duration:
                keys_to_remove.append(position)

        for key in keys_to_remove:
            effect_dict.pop(key)

    def _add_delayed_effects_to_grids(
        self,
        cost: float,
        radius: float,
        effect_dict: Dict,
        react_on_frame: int,
    ) -> None:
        """Add the costs of the delayed effects to the grids.

        Parameters
        ----------
        cost :
            Cost of the effect.
        radius :
            How far around the center position the cost should be added.
        effect_dict :
            Currently tracked effects.
        react_on_frame :
            When units should begin reacting to this effect.

        Returns
        -------

        """
        current_frame: int = self.ai.state.game_loop
        for position, frame_commenced in effect_dict.items():
            frame_difference: int = current_frame - frame_commenced
            if frame_difference >= react_on_frame:
                (
                    self.air_grid,
                    self.air_vs_ground_grid,
                    self.climber_grid,
                    self.ground_grid,
                    self.air_avoidance_grid,
                    self.ground_avoidance_grid,
                    self.priority_ground_avoidance_grid,
                ) = self.add_cost_to_multiple_grids(
                    position,
                    cost,
                    radius + self.config[PATHING][EFFECTS_RANGE_BUFFER],
                    [
                        self.air_grid,
                        self.air_vs_ground_grid,
                        self.climber_grid,
                        self.ground_grid,
                        self.air_avoidance_grid,
                        self.ground_avoidance_grid,
                        self.priority_ground_avoidance_grid,
                    ],
                )

    def _update_delayed_effects(self) -> None:
        """Update manually tracked effects.

        Returns
        -------

        """
        # these effects disappear from the observation, so we have to manually add them
        self._add_delayed_effects_to_grids(
            cost=self.config[PATHING][EFFECTS][CORROSIVE_BILE][COST],
            radius=self.config[PATHING][EFFECTS][CORROSIVE_BILE][RANGE],
            effect_dict=self.biles_dict,
            react_on_frame=self.REACT_TO_BILES_ON_FRAME,
        )
        self._add_delayed_effects_to_grids(
            cost=self.config[PATHING][EFFECTS][NUKE][COST],
            radius=self.config[PATHING][EFFECTS][NUKE][RANGE],
            effect_dict=self.storms_dict,
            react_on_frame=self.REACT_TO_NUKES_ON_FRAME,
        )

        self._clear_delayed_effects(self.biles_dict, self.BILE_DURATION)
        self._clear_delayed_effects(self.storms_dict, self.NUKE_DURATION)
