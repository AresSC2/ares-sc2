"""Enable cross manager communication.

"""

from abc import ABCMeta, abstractmethod
from typing import Any, Callable, DefaultDict, Dict, List, Optional, Set, Tuple, Union

import numpy as np
from sc2.game_info import Ramp
from sc2.ids.unit_typeid import UnitTypeId as UnitID
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units
from scipy.spatial import KDTree

from ares.consts import EngagementResult, ManagerName, ManagerRequestType, UnitRole
from MapAnalyzer import MapData


class IManagerMediator(metaclass=ABCMeta):
    """
    The Mediator interface declares a method used by components to notify the
    mediator about various events. The Mediator may react to these events and
    pass the execution to other components (managers).
    """

    # each manager has a dict linking the request type to a callable action
    manager_requests_dict: Dict[ManagerRequestType, Callable]

    @abstractmethod
    def manager_request(
        self,
        receiver: ManagerName,
        request: ManagerRequestType,
        reason: str = None,
        **kwargs
    ) -> Any:
        """How requests will be structured.

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

        """
        pass


class ManagerMediator(IManagerMediator):
    """
    Mediator concrete class is the single source of truth and coordinator of
    communications between the managers.
    """

    def __init__(self) -> None:
        self.managers: Dict[str, "Manager"] = {}  # noqa

    def add_managers(self, managers: List["Manager"]) -> None:  # noqa
        """Generate manager dictionary.

        Parameters
        ----------
        managers :
            List of all Managers capable of handling ManagerRequests.
        """
        for manager in managers:
            self.managers[str(type(manager).__name__)] = manager

    def manager_request(
        self,
        receiver: ManagerName,
        request: ManagerRequestType,
        reason: str = None,
        **kwargs
    ) -> Any:
        """Function to request information from a manager.

        Parameters
        ----------
        receiver :
            Manager receiving the request.
        request :
            Requested attribute/function call.
        reason :
            Why the request is being made.
        kwargs :
            Keyword arguments (if any) to be passed to the requested function.

        Returns
        -------
        Any :
            There are too many possible return types to list all of them.

        """
        return self.managers[receiver.value].manager_request(
            receiver, request, reason, **kwargs
        )

    """
    Add methods and properties below for commonly used manager requests or for
    readability in other classes
    Format: properties in alphabetical order followed by methods in alphabetical order
    Basically, this can act as an API front end for accessing the managers
    Or eventually requesting the managers calculate something (like a new attack target)

    `manager_request` can also be used
    """

    """
    BuildingManager
    """

    def build_with_specific_worker(self, **kwargs) -> bool:
        """Build a structure with a specific worker.

        BuildingManager.

        Other Parameters
        -----
        worker : Unit
            The chosen worker.
        structure_type : UnitID
            What type of structure to build.
        pos : Point2
            Where the structure should be placed.
        building_purpose : BuildingPurpose
            Why the structure is being placed.

        Parameters
        ----------
        kwargs :
            (See Other Parameters)

        Returns
        -------
        bool :
            True if a position for the building is found and the worker is valid,
            otherwise False

        """
        return self.manager_request(
            ManagerName.BUILDING_MANAGER,
            ManagerRequestType.BUILD_WITH_SPECIFIC_WORKER,
            **kwargs,
        )

    @property
    def get_building_counter(self) -> DefaultDict[UnitID, int]:
        """Get a dictionary containing the number of each type of building in progress.

        BuildingManager.

        Returns
        -------
        DefaultDict[UnitID, int] :
            Number of each type of UnitID presently being tracking for building.

        """
        return self.manager_request(
            ManagerName.BUILDING_MANAGER, ManagerRequestType.GET_BUILDING_COUNTER
        )

    @property
    def get_building_tracker_dict(
        self,
    ) -> Dict[int, Dict[str, Union[Point2, Unit, UnitID, float]]]:
        """Get the building tracker dictionary.

        Building Manager.

        Returns
        -------
        Dict[int, Dict[str, Union[Point2, Unit, UnitID, float]]] :
            Tracks the worker tag to:
                UnitID of the building to be built
                Point2 of where the building is to be placed
                In-game time when the order started
                Why the building is being built

        """
        return self.manager_request(
            ManagerName.BUILDING_MANAGER, ManagerRequestType.GET_BUILDING_TRACKER_DICT
        )

    """
    CombatManager
    """

    @property
    def get_position_of_main_attacking_squad(self) -> Point2:
        """Get the position of the main attacking squad.

        CombatManager

        Returns
        -------
        Point2 :
            Position of the main attacking squad.

        """
        return self.manager_request(
            ManagerName.COMBAT_MANAGER,
            ManagerRequestType.GET_POSITION_OF_MAIN_ATTACKING_SQUAD,
        )

    @property
    def get_predicted_main_fight_result(self) -> EngagementResult:
        """Return the combat sim result between each player's main force.

        Find the main army for each force, and check the combat sim.

        CombatManager

        Returns
        -------
        EngagementResult :
            Predicted combat result between friendly and enemy main forces.

        """
        return self.manager_request(
            ManagerName.COMBAT_MANAGER,
            ManagerRequestType.GET_PREDICTED_MAIN_FIGHT_RESULT,
        )

    @property
    def get_attack_squad_engage_target(self) -> bool:
        """Should the attack squad engage the target?

        Combat Manager

        Returns
        -------
        bool :
            True if the attack squad should engage their target, False otherwise.

        """
        return self.manager_request(
            ManagerName.COMBAT_MANAGER, ManagerRequestType.GET_SQUAD_CLOSE_TO_TARGET
        )

    @property
    def get_mineral_patch_to_list_of_workers(self) -> Dict[int, Set[int]]:
        """Get a dictionary containing mineral tag to worker tags

        Resource Manager

        Returns
        -------
        dict :
            Dictionary where key is mineral tag, and value is workers assigned here.

        """
        return self.manager_request(
            ManagerName.RESOURCE_MANAGER,
            ManagerRequestType.GET_MINERAL_PATCH_TO_LIST_OF_WORKERS,
        )

    @property
    def get_worker_tag_to_townhall_tag(self) -> dict[int, int]:
        """Get a dictionary containing worker tag to townhall tag.
        Where the townhall is the place where worker returns resources

        Resource Manager

        Returns
        -------
        dict :
            Dictionary where key is worker tag, and value is townhall tag.

        """
        return self.manager_request(
            ManagerName.RESOURCE_MANAGER,
            ManagerRequestType.GET_WORKER_TAG_TO_TOWNHALL_TAG,
        )

    @property
    def get_worker_to_mineral_patch_dict(self) -> dict[int, int]:
        """Get a dictionary containing worker tag to mineral patch tag.

        Resource Manager

        Returns
        -------
        dict :
            Dictionary where key is worker tag, and value is mineral tag.

        """
        return self.manager_request(
            ManagerName.RESOURCE_MANAGER,
            ManagerRequestType.GET_WORKER_TO_MINERAL_PATCH_DICT,
        )

    def remove_mineral_field(self, **kwargs) -> None:
        """Request for a mineral field to be removed from bookkeeping.

        Resource Manager

        Other Parameters
        -----
        mineral_field_tag : int
            The tag of the patch to remove.

        Parameters
        ----------
        kwargs :
            (See Other Parameters)
        """
        return self.manager_request(
            ManagerName.RESOURCE_MANAGER,
            ManagerRequestType.REMOVE_MINERAL_FIELD,
            **kwargs,
        )

    @property
    def get_worker_to_vespene_dict(self) -> dict:
        """Get a dictionary containing worker tag to gas building tag.

        Resource Manager

        Returns
        -------
        dict :
            Dictionary where key is worker tag, and value is gas building tag.

        """
        return self.manager_request(
            ManagerName.RESOURCE_MANAGER,
            ManagerRequestType.GET_WORKER_TO_GAS_BUILDING_DICT,
        )

    def remove_gas_building(self, **kwargs) -> None:
        """Request for a gas building to be removed from bookkeeping.

        Resource Manager

        Other Parameters
        -----
        gas_building_tag : int
            The tag of the gas building to remove.

        Parameters
        ----------
        kwargs :
            (See Other Parameters)
        """
        return self.manager_request(
            ManagerName.RESOURCE_MANAGER,
            ManagerRequestType.REMOVE_GAS_BUILDING,
            **kwargs,
        )

    def remove_tag_from_squads(self, **kwargs) -> None:
        """Remove the given tag from unit squads.

        Combat Manager

        Other Parameters
        -----
        tag : int
            The tag of the unit to remove from squads.

        Parameters
        ----------
        kwargs :
            (See Other Parameters)
        """
        return self.manager_request(
            ManagerName.COMBAT_MANAGER,
            ManagerRequestType.REMOVE_TAG_FROM_SQUADS,
            **kwargs,
        )

    """
    PathManager
    """

    def find_closest_safe_spot(self, **kwargs) -> Point2:
        """Find the closest point with the lowest cost on a grid.

        PathManager

        Other Parameters
        -----
        from_pos : Point2
            Where the search starts from.
        grid : np.ndarray
            The grid to find the low cost point on.
        radius : float
            How far away the safe point can be.

        Parameters
        ----------
        kwargs :
            (See Other Parameters)

        Returns
        -------
        Point2 :
            The closest location with the lowest cost.

        """
        return self.manager_request(
            ManagerName.PATH_MANAGER, ManagerRequestType.GET_CLOSEST_SAFE_SPOT, **kwargs
        )

    def find_low_priority_path(self, **kwargs) -> List[Point2]:
        """Find several points in a path.

        This way a unit can queue them up all at once for performance reasons.

        i.e. running drones from a base or sending an overlord to a new position.

        This does not return every point in the path. Instead, it returns points spread
        along the path.

        PathManager

        Other Parameters
        -----
        start : Point2
            Start point of the path.
        target : Point2
            Desired end point of the path.
        grid : np.ndarray
            The grid that should be used for pathing.

        Parameters
        ----------
        kwargs :
            (See Other Parameters)

        Returns
        -------
        List[Point2] :
            List of points composing the path.

        """

        return self.manager_request(
            ManagerName.PATH_MANAGER,
            ManagerRequestType.FIND_LOW_PRIORITY_PATH,
            **kwargs,
        )

    def find_lowest_cost_points(self, **kwargs) -> List[Point2]:
        """Find the point(s) with the lowest cost within `radius` from `from_pos`.

        PathManager

        Other Parameters
        ----------
        from_pos : Point2
            Point to start the search from.
        radius : float
            How far away the returned points can be.
        grid : np.ndarray
            Which grid to query for lowest cost points.

        Parameters
        ----------
        kwargs :
            (See Other Parameters)

        Returns
        -------
        List[Point2] :
            Points with the lowest cost on the grid.

        """
        return self.manager_request(
            ManagerName.PATH_MANAGER,
            ManagerRequestType.FIND_LOWEST_COST_POINTS,
            **kwargs,
        )

    def find_path_next_point(self, **kwargs) -> Point2:
        """Find the next point in a path.

        Other Parameters
        ----------
        start : Point2
            Start point of the path.
        target : Point2
            Desired end point of the path.
        grid : np.ndarray
            The grid that should be used for pathing.
        sensitivity : int, optional
            Amount of points that should be skipped in the full path between tiles that
            are returned.
        smoothing : bool, optional
            Optional path smoothing where nodes are removed if it's possible to jump
            ahead some tiles in a straight line with a lower cost.
        sense_danger : bool, optional
            Check to see if there are any dangerous tiles near the starting point. If
            this is True and there are no dangerous tiles near the starting point, the
            pathing query is skipped and the target is returned.
        danger_distance : float, optional
            How far away from the start to look for danger.
        danger_threshold : float, optional
            Minimum value for a tile to be considered dangerous.

        Parameters
        ----------
        kwargs :
            (See Other Parameters)

        Returns
        -------
        Point2 :
            The next point in the path from the start to the target which may be the
            same as the target if it's safe.

        """
        return self.manager_request(
            ManagerName.PATH_MANAGER, ManagerRequestType.PATH_NEXT_POINT, **kwargs
        )

    def find_raw_path(self, **kwargs) -> List[Point2]:
        """Used for finding a full path, mostly for distance checks.

        PathManager

        Other Parameters
        ----------
        start : Point2
            Start point of the path.
        target : Point2
            Desired end point of the path.
        grid : np.ndarray
            The grid that should be used for pathing.
        sensitivity : int
            Amount of points that should be skipped in the full path between tiles that
            are returned.

        Parameters
        ----------
        kwargs :
            (See Other Parameters)

        Returns
        -------
        List[Point2] :
            List of points composing the path.

        """
        return self.manager_request(
            ManagerName.PATH_MANAGER, ManagerRequestType.FIND_RAW_PATH, **kwargs
        )

    @property
    def get_air_avoidance_grid(self) -> np.ndarray:
        """Get the air avoidance pathing grid.

        PathManager

        Returns
        -------
        np.ndarray :
            The air avoidance pathing grid.

        """
        return self.manager_request(
            ManagerName.PATH_MANAGER, ManagerRequestType.GET_AIR_AVOIDANCE_GRID
        )

    @property
    def get_air_grid(self) -> np.ndarray:
        """Get the air pathing grid.

        PathManager

        Returns
        -------
        np.ndarray :
            The air pathing grid.

        """
        return self.manager_request(
            ManagerName.PATH_MANAGER, ManagerRequestType.GET_AIR_GRID
        )

    @property
    def get_air_vs_ground_grid(self) -> np.ndarray:
        """Get the air vs ground pathing grid.

        PathManager

        Returns
        -------
        np.ndarray :
            The air vs ground pathing grid.

        """
        return self.manager_request(
            ManagerName.PATH_MANAGER, ManagerRequestType.GET_AIR_VS_GROUND_GRID
        )

    @property
    def get_cached_ground_grid(self) -> np.ndarray:
        """Get a non-influence ground pathing grid.

        PathManager

        Returns
        -------
        np.ndarray :
            The clean ground pathing grid.

        """
        return self.manager_request(
            ManagerName.PATH_MANAGER, ManagerRequestType.GET_CACHED_GROUND_GRID
        )

    @property
    def get_forcefield_positions(self) -> List[Point2]:
        """Get positions of forcefields.

        PathManager

        Returns
        -------
        List[Point2] :
            List of the center point of forcefields.

        """
        return self.manager_request(
            ManagerName.PATH_MANAGER,
            ManagerRequestType.GET_FORCEFIELD_POSITIONS,
        )

    @property
    def get_ground_avoidance_grid(self) -> np.ndarray:
        """Get the ground avoidance pathing grid.

        PathManager

        Returns
        -------
        np.ndarray :
            The ground avoidance pathing grid.

        """
        return self.manager_request(
            ManagerName.PATH_MANAGER, ManagerRequestType.GET_GROUND_AVOIDANCE_GRID
        )

    @property
    def get_ground_grid(self) -> np.ndarray:
        """Get the ground pathing grid.

        PathManager

        Returns
        -------
        np.ndarray :
            The ground pathing grid.

        """
        return self.manager_request(
            ManagerName.PATH_MANAGER, ManagerRequestType.GET_GROUND_GRID
        )

    @property
    def get_map_data_object(self) -> MapData:
        """Get the MapAnalyzer.MapData object being used.

        PathManager

        Returns
        -------
        MapData :
            The MapAnalyzer.MapData object being used.

        """
        return self.manager_request(
            ManagerName.PATH_MANAGER, ManagerRequestType.GET_MAP_DATA
        )

    @property
    def get_priority_ground_avoidance_grid(self) -> np.ndarray:
        """Get the pathing grid containing things ground units should always avoid.

        PathManager

        Returns
        -------
        np.ndarray :
            The priority ground avoidance pathing grid.

        """
        return self.manager_request(
            ManagerName.PATH_MANAGER,
            ManagerRequestType.GET_PRIORITY_GROUND_AVOIDANCE_GRID,
        )

    @property
    def get_whole_map_array(self) -> List[List[int]]:
        """Get the list containing every point on the map.

        PathManager

        Notes
        -----
        This does not return Point2s.

        Returns
        -------
        List[List[int]] :
            Every point on the map.

        """
        return self.manager_request(
            ManagerName.PATH_MANAGER, ManagerRequestType.GET_WHOLE_MAP_ARRAY
        )

    @property
    def get_whole_map_tree(self) -> KDTree:
        """Get the KDTree of all points on the map.

        PathManager

        Returns
        -------
        KDTree :
            KDTree of all points on the map.

        """
        return self.manager_request(
            ManagerName.PATH_MANAGER, ManagerRequestType.GET_WHOLE_MAP_TREE
        )

    def is_position_safe(self, **kwargs) -> bool:
        """Check if the given position is considered dangerous.

        PathManager

        Other Parameters
        ----------
        grid : np.ndarray
            The grid to evaluate safety on.
        position : Point2
            The position to check the safety of.
        weight_safety_limit : float
            The maximum value the point can have on the grid to be considered safe.

        Parameters
        ----------
        kwargs :
            (See Other Parameters)

        Returns
        -------
        bool:
            True if the position is considered safe, False otherwise.

        """
        return self.manager_request(
            ManagerName.PATH_MANAGER,
            ManagerRequestType.IS_POSITION_SAFE,
            **kwargs,
        )

    """
    PlacementManager
    """

    def can_place_structure(self, **kwargs) -> bool:
        """Check if structure can be placed at a given position.

        Faster cython alternative to `python-sc2` `await self.can_place()`

        PlacementManager

        Other Parameters
        ----------
        position : Point2
            The intended building position.
        size : BuildingSize
            Size of intended structure.
        include_addon : bool, optional
            For Terran structures, check addon will place too.

        Parameters
        ----------
        kwargs :
            (See Other Parameters)
        Returns
        ----------
        bool :
            Indicating if structure can be placed at given position.
        """
        return self.manager_request(
            ManagerName.PLACEMENT_MANAGER,
            ManagerRequestType.CAN_PLACE_STRUCTURE,
            **kwargs,
        )

    def request_building_placement(self, **kwargs) -> Optional[Point2]:
        """Request a building placement from the precalculated building formation.

        PlacementManager

        Other Parameters
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

        Parameters
        ----------
        kwargs :
            (See Other Parameters)
        Returns
        ----------
        bool :
            Indicating if structure can be placed at given position.
        """
        return self.manager_request(
            ManagerName.PLACEMENT_MANAGER,
            ManagerRequestType.REQUEST_BUILDING_PLACEMENT,
            **kwargs,
        )

    """
    ResourceManager
    """

    @property
    def get_num_available_mineral_patches(self) -> int:
        """Get the number available mineral fields.

        An available mineral field is one that is near a townhall and has fewer than two
        assigned workers.

        ResourceManager

        Returns
        -------
        int :
            Number available mineral fields.

        """
        return self.manager_request(
            ManagerName.RESOURCE_MANAGER,
            ManagerRequestType.GET_NUM_AVAILABLE_MIN_PATCHES,
        )

    def remove_worker_from_mineral(self, **kwargs) -> None:
        """Remove worker from internal data structures.

        This happens if worker gets assigned to do something else

        ResourceManager

        Other Parameters
        ----------
        worker_tag : int
            Tag of the worker to be removed.

        Parameters
        ----------
        kwargs :
            (See Other Parameters)
        """
        return self.manager_request(
            ManagerName.RESOURCE_MANAGER,
            ManagerRequestType.REMOVE_WORKER_FROM_MINERAL,
            **kwargs,
        )

    def select_worker(self, **kwargs) -> Optional[Unit]:
        """Select a worker via the ResourceManager.

        This way we can select one assigned to a far mineral patch.
        Make sure to change the worker role once selected, otherwise it will be selected
        to mine again. This doesn't select workers from geysers, so make sure to remove
        workers from gas if low on workers.

        ResourceManager

        Other Parameters
        ----------
        target_position : Point2
            Location to get the closest workers to.
        force_close : bool
            Select the available worker closest to `target_position` if True.

        Parameters
        ----------
        kwargs :
            (See Other Parameters)

        Returns
        -------
        Optional[Unit] :
            Selected worker, if available.

        """
        return self.manager_request(
            ManagerName.RESOURCE_MANAGER,
            ManagerRequestType.SELECT_WORKER,
            **kwargs,
        )

    """
    StrategyManager
    """

    def can_win_fight(self, **kwargs) -> EngagementResult:
        """Use the combat simulator to predict if our units can beat the enemy units.

        Returns an Enum so that thresholds can be easily adjusted and it may be easier
        to read the results in other code.

        StrategyManager

        Warnings
        --------
        The combat simulator has some bugs in it that I'm not able to fix since they're
        in the Rust code. Notable bugs include Missile Turrets shooting Hydralisks and
        45 SCVs killing a Mutalisk. To get around this, you can filter out units that
        shouldn't be included, such as not including SCVs when seeing if the Mutalisks
        can win a fight (this creates its own problems due to the bounce, but I don't
        believe the bounce is included in the simulation). The simulator isn't perfect,
        but I think it's still usable. My recommendation is to use it cautiously and
        only when all units involved can attack each other. It definitely doesn't factor
        good micro in, so anything involving spell casters is probably a bad idea.

        Other Parameters
        ----------
        own_units : Units
            Friendly units to us in the simulation.
        enemy_units : Units
            Enemy units to us in the simulation.
        timing_adjust : bool
            Take distance between units into account.
        good_positioning : bool
            Assume units are positioned reasonably.

        Parameters
        ----------
        kwargs :
            (See Other Parameters)

        Returns
        -------
        EngagementResult :
            Predicted result of the engagement.

        """
        return self.manager_request(
            ManagerName.STRATEGY_MANAGER,
            ManagerRequestType.CAN_WIN_FIGHT,
            **kwargs,
        )

    @property
    def get_enemy_at_home(self) -> bool:
        """Get whether the enemy is near their main or natural base.

        StrategyManager

        Returns
        -------
        bool :
            True if the enemy army center mass is near their main or natural base, False
            otherwise.

        """
        return self.manager_request(
            ManagerName.STRATEGY_MANAGER,
            ManagerRequestType.GET_ENEMY_AT_HOME,
        )

    @property
    def get_mineral_target_dict(self) -> dict[int, Point2]:
        """Get position in front of each mineral.

        This position is used for speed mining, and is also useful for
        making sure worker is moved to the right side of a mineral.

        ResourceManager

        Returns
        -------
        dict :
            Key -> mineral tag, Value -> Position

        """
        return self.manager_request(
            ManagerName.RESOURCE_MANAGER,
            ManagerRequestType.GET_MINERAL_TARGET_DICT,
        )

    @property
    def get_offensive_attack_target(self) -> Point2:
        """Get the current offensive attack target.

        StrategyManager

        Returns
        -------
        Point2 :
            The current offensive attack target.

        """
        return self.manager_request(
            ManagerName.STRATEGY_MANAGER, ManagerRequestType.GET_OFFENSIVE_ATTACK_TARGET
        )

    @property
    def get_rally_point(self) -> Point2:
        """Get the rally point for units.

        StrategyManager

        Returns
        -------
        Point2 :
            Position to use as a rally point.

        """
        return self.manager_request(
            ManagerName.STRATEGY_MANAGER, ManagerRequestType.GET_RALLY_POINT
        )

    @property
    def get_should_be_offensive(self) -> bool:
        """Get whether we should launch an offensive attack.

        StrategyManager

        Returns
        -------
        bool :
            True if we should launch an attack, False otherwise.

        """
        return self.manager_request(
            ManagerName.STRATEGY_MANAGER, ManagerRequestType.GET_SHOULD_BE_OFFENSIVE
        )

    """
    TerrainManager
    """

    def building_position_blocked_by_burrowed_unit(self, **kwargs) -> Optional[Point2]:
        """See if the building position is blocked by a burrowed unit.

        TerrainManager

        Other Parameters
        ----------
        worker_tag : int
            The worker attempting to build the structure.
        position : Point2
            Where the structure is attempting to be placed.

        Parameters
        ----------
        kwargs :
            (See Other Parameters)

        Returns
        -------
        Optional[Point2] :
            The position that's blocked by an enemy unit.

        """
        return self.manager_request(
            ManagerName.TERRAIN_MANAGER,
            ManagerRequestType.BUILDING_POSITION_BLOCKED_BY_BURROWED_UNIT,
            **kwargs,
        )

    def get_behind_mineral_positions(self, **kwargs) -> List[Point2]:
        """Finds 3 spots behind the mineral line

        This is useful for building structures out of typical cannon range.

        TerrainManager

        Other Parameters
        ----------
        th_pos : Point2
            Position of townhall to find points behind the mineral line of.

        Parameters
        ----------
        kwargs :
            (See Other Parameters)

        Returns
        -------
        List[Point2] :
            Points behind the mineral line of the designated base.

        """
        return self.manager_request(
            ManagerName.TERRAIN_MANAGER,
            ManagerRequestType.GET_BEHIND_MINERAL_POSITIONS,
            **kwargs,
        )

    def get_closest_overlord_spot(self, **kwargs) -> Point2:
        """Given a position, find the closest high ground overlord spot.

        TerrainManager

        Other Parameters
        ----------
        from_pos : Point2
            Position the Overlord spot should be closest to.

        Parameters
        ----------
        kwargs :
            (See Other Parameters)

        Returns
        -------
        Point2 :
            The closest Overlord hiding spot to the position.

        """
        return self.manager_request(
            ManagerName.TERRAIN_MANAGER,
            ManagerRequestType.GET_CLOSEST_OVERLORD_SPOT,
            **kwargs,
        )

    @property
    def get_defensive_third(self) -> Point2:
        """Get the third furthest from enemy.

        TerrainManager

        Returns
        -------
        Point2 :
            Location of the third base furthest from the enemy.

        """
        return self.manager_request(
            ManagerName.TERRAIN_MANAGER, ManagerRequestType.GET_DEFENSIVE_THIRD
        )

    @property
    def get_enemy_expansions(self) -> List[Tuple[Point2, float]]:
        """Get the expansions, as ordered from the enemy's point of view.

        TerrainManager

        Returns
        -------
        List[Tuple[Point2, float]] :
            List of Tuples where
                The first element is the location of the base.
                The second element is the pathing distance from the enemy main base.

        """
        return self.manager_request(
            ManagerName.TERRAIN_MANAGER, ManagerRequestType.GET_ENEMY_EXPANSIONS
        )

    @property
    def get_enemy_fourth(self) -> Point2:
        """Get the enemy fourth base.

        TerrainManager

        Returns
        -------
        Point2 :
            Location of the enemy fourth base.

        """
        return self.manager_request(
            ManagerName.TERRAIN_MANAGER, ManagerRequestType.GET_ENEMY_FOURTH
        )

    @property
    def get_enemy_nat(self) -> Point2:
        """Get the enemy natural expansion.

        TerrainManager

        Returns
        -------
        Point2 :
            Location of the enemy natural expansion.

        """
        return self.manager_request(
            ManagerName.TERRAIN_MANAGER, ManagerRequestType.GET_ENEMY_NAT
        )

    @property
    def get_enemy_ramp(self) -> Ramp:
        """Get the enemy main base ramp.

        TerrainManager

        Returns
        -------
        Ramp :
            sc2 Ramp object for the enemy main base ramp.

        """
        return self.manager_request(
            ManagerName.TERRAIN_MANAGER, ManagerRequestType.GET_ENEMY_RAMP
        )

    @property
    def get_enemy_third(self) -> Point2:
        """Get the enemy third base.

        TerrainManager

        Returns
        -------
        Point2 :
            Location of the enemy third base.

        """
        return self.manager_request(
            ManagerName.TERRAIN_MANAGER, ManagerRequestType.GET_ENEMY_THIRD
        )

    def get_flood_fill_area(self, **kwargs) -> set[tuple[int, int]]:
        """Given a point, flood fill outward from it and return the valid points.

        This flood fill does not continue through chokes.

        TerrainManager

        Other Parameters
        -----
        start_point : Point2
            Where to start the flood fill.
        max_dist : float
            Only include points closer than this distance to the start point.

        Parameters
        ----------
        kwargs :
            (See Other Parameters)

        Returns
        -------
        Tuple[int, List[Tuple[int, int]]] :
            First element is the number of valid points.
            Second element is the list of all valid points.

        """
        return self.manager_request(
            ManagerName.TERRAIN_MANAGER,
            ManagerRequestType.GET_FLOOD_FILL_AREA,
            **kwargs,
        )

    @property
    def get_initial_pathing_grid(self) -> np.ndarray:
        """Get the pathing grid as it was on the first iteration.

        TerrainManager

        Returns
        -------
        np.ndarray :
            The pathing grid as it was on the first iteration.

        """
        return self.manager_request(
            ManagerName.TERRAIN_MANAGER, ManagerRequestType.GET_INITIAL_PATHING_GRID
        )

    @property
    def get_is_free_expansion(self) -> bool:
        """Check all bases for a free expansion.

        TerrainManager

        Returns
        -------
        bool :
            True if there exists a free expansion, False otherwise.

        """
        return self.manager_request(
            ManagerName.TERRAIN_MANAGER, ManagerRequestType.GET_IS_FREE_EXPANSION
        )

    @property
    def get_map_choke_points(self) -> Set[Point2]:
        """All the points on the map that compose choke points.

        TerrainManager

        Returns
        -------
        Set[Point2] :
            All the points on the map that compose choke points.

        """
        return self.manager_request(
            ManagerName.TERRAIN_MANAGER,
            ManagerRequestType.GET_MAP_CHOKE_POINTS,
        )

    @property
    def get_ol_spot_near_enemy_nat(self) -> Point2:
        """Get the overlord spot nearest to the enemy natural.

        TerrainManager

        Returns
        -------
        Point2 :
            Overlord spot near the enemy natural.

        """
        return self.manager_request(
            ManagerName.TERRAIN_MANAGER,
            ManagerRequestType.GET_OL_SPOT_NEAR_ENEMY_NATURAL,
        )

    @property
    def get_ol_spots(self) -> List[Point2]:
        """High ground Overlord hiding spots.

        TerrainManager

        Returns
        -------
        List[Point2] :
            List of Overlord hiding spots.

        """
        return self.manager_request(
            ManagerName.TERRAIN_MANAGER,
            ManagerRequestType.GET_OL_SPOTS,
        )

    @property
    def get_own_expansions(self) -> List[Tuple[Point2, float]]:
        """Get the expansions.

        TerrainManager

        Returns
        -------
        List[Tuple[Point2, float]] :
            List of Tuples where
                The first element is the location of the base.
                The second element is the pathing distance from our main base.

        """
        return self.manager_request(
            ManagerName.TERRAIN_MANAGER, ManagerRequestType.GET_OWN_EXPANSIONS
        )

    @property
    def get_own_nat(self) -> Point2:
        """Get our natural expansion.

        TerrainManager

        Returns
        -------
        Point2 :
            Location of our natural expansion.

        """
        return self.manager_request(
            ManagerName.TERRAIN_MANAGER, ManagerRequestType.GET_OWN_NAT
        )

    @property
    def get_positions_blocked_by_burrowed_enemy(self) -> List[Point2]:
        """Build positions that are blocked by a burrowed enemy unit.

        TerrainManager

        Returns
        -------
        List[Point2] :
            List of build positions that are blocked by a burrowed enemy unit.

        """
        return self.manager_request(
            ManagerName.TERRAIN_MANAGER,
            ManagerRequestType.GET_POSITIONS_BLOCKED_BY_BURROWED_ENEMY,
        )

    """
    UnitCacheManager
    """

    @property
    def get_cached_enemy_army(self) -> Units:
        """Get the Units object for the enemy army.

        UnitCacheManager

        Returns
        -------
        Units :
            The enemy army.

        """
        return self.manager_request(
            ManagerName.UNIT_CACHE_MANAGER, ManagerRequestType.GET_CACHED_ENEMY_ARMY
        )

    @property
    def get_cached_enemy_workers(self) -> Units:
        """Get the Units object for the enemy workers.

        UnitCacheManager

        Returns
        -------
        Units :
            The enemy workers.

        """
        return self.manager_request(
            ManagerName.UNIT_CACHE_MANAGER, ManagerRequestType.GET_CACHED_ENEMY_WORKERS
        )

    @property
    def get_enemy_army_center_mass(self) -> Point2:
        """Get the point containing the largest amount of the enemy army.

        UnitCacheManager

        Returns
        -------
        Point2 :
            Enemy army center mass location.

        """
        return self.manager_request(
            ManagerName.UNIT_CACHE_MANAGER,
            ManagerRequestType.GET_ENEMY_ARMY_CENTER_MASS,
        )

    @property
    def get_enemy_army_dict(self) -> DefaultDict[UnitID, Units]:
        """Get the dictionary of enemy army unit types to the units themselves.

        UnitCacheManager

        Returns
        -------
        DefaultDict[UnitID, Units] :
            The dictionary of enemy army unit types to the units themselves.

        """
        return self.manager_request(
            ManagerName.UNIT_CACHE_MANAGER,
            ManagerRequestType.GET_CACHED_ENEMY_ARMY_DICT,
        )

    @property
    def get_old_own_army_dict(self) -> Dict[UnitID, Units]:
        """Get the previous iteration's `own_army` dict.

        UnitCacheManager

        Returns
        -------
        DefaultDict[UnitID, Units] :
            The dictionary of own army unit types to the units themselves.

        """
        return self.manager_request(
            ManagerName.UNIT_CACHE_MANAGER, ManagerRequestType.GET_OLD_OWN_ARMY_DICT
        )

    @property
    def get_own_army(self) -> Units:
        """Get the Units object for our own army.

        UnitCacheManager

        Returns
        -------
        Units :
            Our own army.

        """
        return self.manager_request(
            ManagerName.UNIT_CACHE_MANAGER, ManagerRequestType.GET_CACHED_OWN_ARMY
        )

    @property
    def get_own_army_dict(self) -> Dict[UnitID, Units]:
        """Get the dictionary of own army unit types to the units themselves.

        UnitCacheManager

        Returns
        -------
        DefaultDict[UnitID, Units] :
            The dictionary of own army unit types to the units themselves.

        """
        return self.manager_request(
            ManagerName.UNIT_CACHE_MANAGER, ManagerRequestType.GET_CACHED_OWN_ARMY_DICT
        )

    @property
    def get_own_structures_dict(self) -> DefaultDict[UnitID, Units]:
        """Get the dictionary of own structure types to the units themselves.

        UnitCacheManager

        Returns
        -------
        DefaultDict[UnitID, Units] :
            The dictionary of own structure types to the units themselves.

        """
        return self.manager_request(
            ManagerName.UNIT_CACHE_MANAGER, ManagerRequestType.GET_OWN_STRUCTURES_DICT
        )

    def get_units_from_tags(self, **kwargs) -> List[Unit]:
        """Get a `list` of `Unit` objects corresponding to the given tags.

        UnitCacheManager

        Other Parameters
        -----
        tags : Set[int]
            Tags of the units to retrieve.

        Parameters
        ----------
        kwargs :
            (See Other Parameters)
        """
        return self.manager_request(
            ManagerName.UNIT_CACHE_MANAGER,
            ManagerRequestType.GET_UNITS_FROM_TAGS,
            **kwargs,
        )

    @property
    def get_removed_units(self) -> Units:
        """Get the units removed from memory units.

        UnitCacheManager

        Returns
        -------
        Units :
            The units removed from memory units.

        """
        return self.manager_request(
            ManagerName.UNIT_CACHE_MANAGER, ManagerRequestType.GET_REMOVED_UNITS
        )

    """
    UnitMemoryManager
    """

    @property
    def get_all_enemy(self) -> Units:
        """Get all enemy units.

        UnitMemoryManager

        Returns
        -------
        Units :
            All enemy units.

        """
        return self.manager_request(
            ManagerName.UNIT_MEMORY_MANAGER, ManagerRequestType.GET_ALL_ENEMY
        )

    @property
    def get_enemy_ground(self) -> Units:
        """Get enemy ground units.

        UnitMemoryManager

        Returns
        -------
        Units :
            Enemy ground units.

        """
        return self.manager_request(
            ManagerName.UNIT_MEMORY_MANAGER, ManagerRequestType.GET_ENEMY_GROUND
        )

    @property
    def get_enemy_fliers(self) -> Units:
        """Get enemy flying units.

        UnitMemoryManager

        Returns
        -------
        Units :
            Enemy flying units.

        """
        return self.manager_request(
            ManagerName.UNIT_MEMORY_MANAGER, ManagerRequestType.GET_ENEMY_FLIERS
        )

    @property
    def get_enemy_tree(self) -> KDTree:
        """Get the KDTree representing all enemy unit positions.

        UnitMemoryManager

        Returns
        -------
        KDTree :
            KDTree representing all enemy unit positions.

        """
        return self.manager_request(
            ManagerName.UNIT_MEMORY_MANAGER, ManagerRequestType.GET_ENEMY_TREE
        )

    def get_units_in_range(
        self, **kwargs
    ) -> Union[Dict[Union[int, Tuple[float, float]], Units], List[Units]]:
        """Get units in range of other units or points.

        UnitMemoryManager

        Other Parameters
        -----
        start_points: List[Union[Unit, Tuple[float, float]]]
            List of `Unit`s or positions to search for units from.
        distances: Union[float, List[float]]
            How far away from each point to query. Must broadcast to the length of
            `start_points`
        query_tree: UnitTreeQueryType
            Which KDTree should be queried.
        return_as_dict: bool = False
            Sets whether the returned units in range should be a dictionary or list.

        Parameters
        ----------
        kwargs :
            (See Other Parameters)

        Returns
        -------
        Union[Dict[Union[int, Tuple[float, float]], Units], List[Units]] :
            Returns the units in range of each start point as a `dict` where the key
            is the unit tag or position and the value is the `Units` in range or a
            `list` of `Units`.

        """
        return self.manager_request(
            ManagerName.UNIT_MEMORY_MANAGER,
            ManagerRequestType.GET_UNITS_IN_RANGE,
            **kwargs,
        )

    @property
    def get_own_tree(self) -> Units:
        """Get the KDTree representing all friendly unit positions.

        UnitMemoryManager

        Returns
        -------
        KDTree :
            KDTree representing all friendly unit positions.

        """
        return self.manager_request(
            ManagerName.UNIT_MEMORY_MANAGER, ManagerRequestType.GET_OWN_TREE
        )

    """
    UnitRoleManager
    """

    def assign_role(self, **kwargs) -> None:
        """Assign a unit a role.

        UnitRoleManager

        Other Parameters
        -----
        tag : int
            Tag of the unit to be assigned.
        role : UnitRole
            What role the unit should have.

        Parameters
        ----------
        kwargs :
            (See Other Parameters)
        """
        return self.manager_request(
            ManagerName.UNIT_ROLE_MANAGER,
            ManagerRequestType.ASSIGN_ROLE,
            **kwargs,
        )

    def batch_assign_role(self, **kwargs) -> None:
        """Assign a given role to a List of unit tags.

        Nothing more than a for loop, provided for convenience.

        UnitRoleManager

        Other Parameters
        -----
        tags : Set[int]
            Tags of the units to assign to a role.
        role : UnitRole
            The role the units should be assigned to.

        Parameters
        ----------
        kwargs :
            (See Other Parameters)
        """
        return self.manager_request(
            ManagerName.UNIT_ROLE_MANAGER,
            ManagerRequestType.BATCH_ASSIGN_ROLE,
            **kwargs,
        )

    def clear_role(self, **kwargs) -> None:
        """Clear a unit's role.

        UnitRoleManager

        Other Parameters
        -----
        tag : int
            Tag of the unit to clear the role of.

        Parameters
        ----------
        kwargs :
            (See Other Parameters)
        """
        return self.manager_request(
            ManagerName.UNIT_ROLE_MANAGER, ManagerRequestType.CLEAR_ROLE, **kwargs
        )

    def get_all_from_roles_except(self, **kwargs) -> Units:
        """Get all units from the given roles except for unit types in excluded.

        UnitRoleManager

        Other Parameters
        -----
        roles : Set[UnitRole]
            Roles to get units from.
        excluded : Set[UnitTypeId]
            Unit types that should not be included.

        Parameters
        ----------
        kwargs :
            (See Other Parameters)

        Returns
        -------
        Units :
            Units matching the role that are not of an excluded type.

        """
        return self.manager_request(
            ManagerName.UNIT_ROLE_MANAGER,
            ManagerRequestType.GET_ALL_FROM_ROLES_EXCEPT,
            **kwargs,
        )

    @property
    def get_unit_role_dict(self) -> Dict[UnitRole, Set[int]]:
        """Get the dictionary of `UnitRole` to the set of tags of units with that role.

        UnitRoleManager

        Returns
        -------
        Dict[UnitRole, Set[int]] :
            Dictionary of `UnitRole` to the set of tags of units with that role.

        """
        return self.manager_request(
            ManagerName.UNIT_ROLE_MANAGER, ManagerRequestType.GET_UNIT_ROLE_DICT
        )

    def get_units_from_role(self, **kwargs) -> Units:
        """Get a Units object containing units with a given role.

        If a UnitID or set of UnitIDs are given, it will only return units of those
        types, otherwise it will return all units with the role. If `restrict_to` is
        specified, it will only retrieve units from that object.

        UnitRoleManager

        Other Parameters
        -----
        role : UnitRole
            Role to get units from.
        unit_type : UnitTypeId
            Type(s) of units that should be returned. If omitted, all units with the
            role will be returned.
        restrict_to : Set[UnitTypeId]
            If supplied, only take Units with the given role and type if they also exist
            here.

        Parameters
        ----------
        kwargs :
            (See Other Parameters)

        Returns
        -------
        Units :
            Units with the given role.

        """
        return self.manager_request(
            ManagerName.UNIT_ROLE_MANAGER,
            ManagerRequestType.GET_UNITS_FROM_ROLE,
            **kwargs,
        )

    def get_units_from_roles(self, **kwargs) -> Units:
        """Get the units matching `unit_type` from the given roles.

        UnitRoleManager

        Other Parameters
        -----
        roles : Set[UnitRole]
            Roles to get units from.
        unit_type : UnitTypeId
            Type(s) of units that should be returned. If omitted, all units with the
            role will be returned.

        Parameters
        ----------
        kwargs :
            (See Other Parameters)

        Returns
        -------
        Units :
            Units with the given roles.
        """
        return self.manager_request(
            ManagerName.UNIT_ROLE_MANAGER,
            ManagerRequestType.GET_UNITS_FROM_ROLES,
            **kwargs,
        )

    def set_workers_per_gas(self, **kwargs) -> None:
        """Give all units in a role a different role.

        ResourceManager

        Other Parameters
        -----
        amount : int
            Num workers to assign to each gas building

        Parameters
        ----------
        kwargs :
            (See Other Parameters)
        """
        return self.manager_request(
            ManagerName.RESOURCE_MANAGER,
            ManagerRequestType.SET_WORKERS_PER_GAS,
            **kwargs,
        )

    def switch_roles(self, **kwargs) -> None:
        """Give all units in a role a different role.

        UnitRoleManager

        Other Parameters
        -----
        from_role : UnitRole
            Role the units currently have.
        to_role : UnitRole
            Role to assign to the units.

        Parameters
        ----------
        kwargs :
            (See Other Parameters)
        """
        return self.manager_request(
            ManagerName.UNIT_ROLE_MANAGER,
            ManagerRequestType.SWITCH_ROLES,
            **kwargs,
        )
