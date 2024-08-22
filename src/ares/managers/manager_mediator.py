"""Enable cross manager communication.

"""

from abc import ABCMeta, abstractmethod
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    DefaultDict,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    Union,
)

import numpy as np
from map_analyzer import MapData
from sc2.game_info import Ramp
from sc2.ids.unit_typeid import UnitTypeId as UnitID
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units
from scipy.spatial import KDTree

from ares.consts import EngagementResult, ManagerName, ManagerRequestType, UnitRole

if TYPE_CHECKING:
    from ares.managers.squad_manager import UnitSquad


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
        Returns
        ----------
        None
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
    AbilityTrackerManager
    """

    @property
    def get_unit_to_ability_dict(self) -> dict[int, Any]:
        """Get a dictionary containing unit tag, to ability frame cooldowns.

        AbilityTrackerManager.

        Returns
        -------
        Dict[int, Any] :
            Unit tag to abilities and the next frame they can be casted.

        """
        return self.manager_request(
            ManagerName.ABILITY_TRACKER_MANAGER,
            ManagerRequestType.GET_UNIT_TO_ABILITY_DICT,
        )

    def update_unit_to_ability_dict(self, **kwargs):
        """Update tracking to reflect ability usage.

        After a unit uses an ability it should call this to update the frame the
        ability will next be available

        AbilityTrackerManager.

        Parameters
        ----------
        ability : AbilityId
            The AbilityId that was used.
        unit_tag : int
            The tag of the Unit that used the ability

        Returns
        ----------
        None

        """
        return self.manager_request(
            ManagerName.ABILITY_TRACKER_MANAGER,
            ManagerRequestType.UPDATE_UNIT_TO_ABILITY_DICT,
            **kwargs,
        )

    """
    BuildingManager
    """

    def build_with_specific_worker(self, **kwargs) -> bool:
        """Build a structure with a specific worker.

        BuildingManager.

        Parameters
        -----
        worker : Unit
            The chosen worker.
        structure_type : UnitID
            What type of structure to build.
        pos : Point2
            Where the structure should be placed.
        building_purpose : BuildingPurpose
            Why the structure is being placed.

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

    def cancel_structure(self, **kwargs) -> None:
        """Cancel a structure and remove from internal ares bookkeeping.

        If you try cancelling without calling this method, ares may try
        to keep rebuilding the cancelled structure.

        BuildingManager.

        Parameters
        ----------
        structure : UnitTypeIdId
            The AbilityId that was used.

        Returns
        ----------
        None
        """
        return self.manager_request(
            ManagerName.BUILDING_MANAGER,
            ManagerRequestType.CANCEL_STRUCTURE,
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
    CombatSimManager
    """

    def can_win_fight(self, **kwargs) -> EngagementResult:
        """Get the predicted engagement result between two forces.

        Combat Sim Manager.

        Parameters
        ----------
        own_units : Units
            Our units involved in the battle.
        enemy_units : Units
            The enemy units.
        timing_adjust : bool
            Take distance between units into account.
        good_positioning : bool
            Assume units are decently split.
        workers_do_no_damage : bool
            Don't take workers into account.

        Returns
        -------
        EngagementResult :
            Enum with human-readable engagement result

        """
        return self.manager_request(
            ManagerName.COMBAT_SIM_MANAGER, ManagerRequestType.CAN_WIN_FIGHT, **kwargs
        )

    """
    EnemyToBaseManager
    """

    @property
    def get_flying_enemy_near_bases(self) -> dict[int, set[int]]:
        """Get dictionary containing flying enemy near townhalls.

        EnemyToBase Manager

        Returns
        -------
        dict[int, set[int]] :
            A dictionary where the integer key is a townhall tag.
            And the value contains a set of ints cotianing enemy tags
            near this base.
        """
        return self.manager_request(
            ManagerName.ENEMY_TO_BASE_MANAGER,
            ManagerRequestType.GET_FLYING_ENEMY_NEAR_BASES,
        )

    @property
    def get_ground_enemy_near_bases(self, **kwargs) -> dict[int, set[int]]:
        """Get dictionary containing ground enemy near townhalls.

        EnemyToBase Manager

        Returns
        -------
        dict[int, set[int]] :
            A dictionary where the integer key is a townhall tag.
            And the value contains a set of ints cotianing enemy tags
            near this base.
        """
        return self.manager_request(
            ManagerName.ENEMY_TO_BASE_MANAGER,
            ManagerRequestType.GET_GROUND_ENEMY_NEAR_BASES,
            **kwargs,
        )

    @property
    def get_main_air_threats_near_townhall(self) -> Units:
        """Get the main enemy air force near one of our bases.

        EnemyToBase Manager

        Returns
        -------
        Units :
            The largest enemy air force near our bases.
        """
        return self.manager_request(
            ManagerName.ENEMY_TO_BASE_MANAGER,
            ManagerRequestType.GET_MAIN_AIR_THREATS_NEAR_TOWNHALL,
        )

    @property
    def get_main_ground_threats_near_townhall(self) -> Units:
        """Get the main enemy ground force near one of our bases.

        EnemyToBase Manager

        Returns
        -------
        Units :
            The largest enemy ground force near our bases.
        """
        return self.manager_request(
            ManagerName.ENEMY_TO_BASE_MANAGER,
            ManagerRequestType.GET_MAIN_GROUND_THREATS_NEAR_TOWNHALL,
        )

    @property
    def get_th_tag_with_largest_ground_threat(self) -> int:
        """Get the tag of our townhall with the largest enemy ground force nearby.

        WARNING: This will remember the townhall tag even if enemy has gone.
        Do not use this to detect enemy at a base.
        Use `get_main_ground_threats_near_townhall`
        Or `get_ground_enemy_near_bases` instead

        EnemyToBase Manager

        Returns
        -------
        Units :
            The largest enemy ground force near our bases.
        """
        return self.manager_request(
            ManagerName.ENEMY_TO_BASE_MANAGER,
            ManagerRequestType.GET_TH_TAG_WITH_LARGEST_GROUND_THREAT,
        )

    """
    IntelManager
    """

    @property
    def get_enemy_expanded(self) -> bool:
        """Has the enemy expanded?

        WARNING: Opinionated method, please write your own if you don't
        agree with this decision.

        Intel Manager

        Returns
        -------
        bool

        """
        return self.manager_request(
            ManagerName.INTEL_MANAGER, ManagerRequestType.GET_ENEMY_EXPANDED
        )

    @property
    def get_enemy_four_gate(self) -> bool:
        """Has the enemy gone four gate?

        WARNING: Opinionated method, please write your own if you don't
        agree with this decision.

        Intel Manager

        Returns
        -------
        bool

        """
        return self.manager_request(
            ManagerName.INTEL_MANAGER, ManagerRequestType.GET_ENEMY_FOUR_GATE
        )

    @property
    def get_enemy_has_base_outside_natural(self) -> bool:
        """Has the enemy expanded outside of their natural?

        WARNING: Opinionated method, please write your own if you don't
        agree with this decision.

        Intel Manager

        Returns
        -------
        bool

        """
        return self.manager_request(
            ManagerName.INTEL_MANAGER,
            ManagerRequestType.GET_ENEMY_HAS_BASE_OUTSIDE_NATURAL,
        )

    @property
    def get_enemy_ling_rushed(self) -> bool:
        """Has the enemy ling rushed?

        WARNING: Opinionated method, please write your own if you don't
        agree with this decision.

        Intel Manager

        Returns
        -------
        bool

        """
        return self.manager_request(
            ManagerName.INTEL_MANAGER, ManagerRequestType.GET_ENEMY_LING_RUSHED
        )

    @property
    def get_enemy_marine_rush(self) -> bool:
        """Is the enemy currently marine rushing?

        WARNING: Opinionated method, please write your own if you don't
        agree with this decision.

        Intel Manager

        Returns
        -------
        bool

        """
        return self.manager_request(
            ManagerName.INTEL_MANAGER, ManagerRequestType.GET_ENEMY_MARINE_RUSH
        )

    @property
    def get_enemy_marauder_rush(self) -> bool:
        """Is the enemy currently marauder rushing?

        WARNING: Opinionated method, please write your own if you don't
        agree with this decision.

        Intel Manager

        Returns
        -------
        bool

        """
        return self.manager_request(
            ManagerName.INTEL_MANAGER, ManagerRequestType.GET_ENEMY_MARAUDER_RUSH
        )

    @property
    def get_enemy_ravager_rush(self) -> Point2:
        """Has the enemy ravager rushed?

        WARNING: Opinionated method, please write your own if you don't
        agree with this decision.

        Intel Manager

        Returns
        -------
        bool

        """
        return self.manager_request(
            ManagerName.INTEL_MANAGER, ManagerRequestType.GET_ENEMY_RAVAGER_RUSH
        )

    @property
    def get_enemy_roach_rushed(self) -> Point2:
        """Did the enemy roach rush?

        WARNING: Opinionated method, please write your own if you don't
        agree with this decision.

        Intel Manager

        Returns
        -------
        bool

        """
        return self.manager_request(
            ManagerName.INTEL_MANAGER, ManagerRequestType.GET_ENEMY_ROACH_RUSHED
        )

    @property
    def get_enemy_was_greedy(self) -> Point2:
        """Was the enemy greedy?

        WARNING: Opinionated method, please write your own if you don't
        agree with this decision.

        Intel Manager

        Returns
        -------
        bool

        """
        return self.manager_request(
            ManagerName.INTEL_MANAGER, ManagerRequestType.GET_ENEMY_WAS_GREEDY
        )

    @property
    def get_enemy_went_four_gate(self) -> Point2:
        """The enemy went four gate this game?

        WARNING: Opinionated method, please write your own if you don't
        agree with this decision.

        Intel Manager

        Returns
        -------
        bool

        """
        return self.manager_request(
            ManagerName.INTEL_MANAGER, ManagerRequestType.GET_ENEMY_WENT_FOUR_GATE
        )

    @property
    def get_enemy_went_marine_rush(self) -> Point2:
        """The enemy went marine rush this game?

        WARNING: Opinionated method, please write your own if you don't
        agree with this decision.

        Intel Manager

        Returns
        -------
        bool

        """
        return self.manager_request(
            ManagerName.INTEL_MANAGER, ManagerRequestType.GET_ENEMY_WENT_MARINE_RUSH
        )

    @property
    def get_enemy_went_marauder_rush(self) -> Point2:
        """The enemy went marauder rush this game?

        WARNING: Opinionated method, please write your own if you don't
        agree with this decision.

        Intel Manager

        Returns
        -------
        bool

        """
        return self.manager_request(
            ManagerName.INTEL_MANAGER, ManagerRequestType.GET_ENEMY_WENT_MARAUDER_RUSH
        )

    @property
    def get_enemy_went_reaper(self) -> Point2:
        """The enemy opened with reaper this game?

        WARNING: Opinionated method, please write your own if you don't
        agree with this decision.

        Intel Manager

        Returns
        -------
        bool

        """
        return self.manager_request(
            ManagerName.INTEL_MANAGER, ManagerRequestType.GET_ENEMY_WENT_REAPER
        )

    @property
    def get_enemy_worker_rushed(self) -> Point2:
        """The enemy went for a worker rush this game?

        WARNING: Opinionated method, please write your own if you don't
        agree with this decision.

        Intel Manager

        Returns
        -------
        bool

        """
        return self.manager_request(
            ManagerName.INTEL_MANAGER, ManagerRequestType.GET_ENEMY_WORKER_RUSHED
        )

    @property
    def get_is_proxy_zealot(self) -> bool:
        """There is currently proxy zealot attempt from enemy?

        WARNING: Opinionated method, please write your own if you don't
        agree with this decision.

        Intel Manager

        Returns
        -------
        bool

        """
        return self.manager_request(
            ManagerName.INTEL_MANAGER, ManagerRequestType.GET_IS_PROXY_ZEALOT
        )

    """
    FlyingStructureManager
    """

    @property
    def get_flying_structure_tracker(self) -> dict[int, Any]:
        """Get the current information stored by FlyingStructureManager.

        FlyingStructureManager

        Returns
        -------
        dict[int, Any] :
            Key -> structure_tag, Value -> Information about the flight.
        """
        return self.manager_request(
            ManagerName.FLYING_STRUCTURE_MANAGER,
            ManagerRequestType.GET_FLYING_STRUCTURE_TRACKER,
        )

    def move_structure(self, **kwargs) -> None:
        """Request a structure to move via flight.

        FlyingStructureManager

        Parameters
        ----------
        structure : Unit
            Our units involved in the battle.
        target : Point2
            The enemy units.
        should_land : bool, optional
            Take distance between units into account.

        Returns
        ----------
        None
        """
        return self.manager_request(
            ManagerName.FLYING_STRUCTURE_MANAGER,
            ManagerRequestType.MOVE_STRUCTURE,
            **kwargs,
        )

    """
    ResourceManager
    """

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

        Parameters
        -----
        mineral_field_tag : int
            The tag of the patch to remove.

        Returns
        ----------
        None
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

        Parameters
        -----
        gas_building_tag : int
            The tag of the gas building to remove.

        Returns
        ----------
        None
        """
        return self.manager_request(
            ManagerName.RESOURCE_MANAGER,
            ManagerRequestType.REMOVE_GAS_BUILDING,
            **kwargs,
        )

    """
    PathManager
    """

    def find_closest_safe_spot(self, **kwargs) -> Point2:
        """Find the closest point with the lowest cost on a grid.

        PathManager

        Parameters
        -----
        from_pos : Point2
            Where the search starts from.
        grid : np.ndarray
            The grid to find the low cost point on.
        radius : float
            How far away the safe point can be.

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

        Parameters
        ----------
        start : Point2
            Start point of the path.
        target : Point2
            Desired end point of the path.
        grid : np.ndarray
            The grid that should be used for pathing.

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

        Parameters
        ----------
        from_pos : Point2
            Point to start the search from.
        radius : float
            How far away the returned points can be.
        grid : np.ndarray
            Which grid to query for lowest cost points.

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

        Parameters
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

        Parameters
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

        Example:
        ```py
        import numpy as np

        avoidance_grid: np.ndarray = self.mediator.get_air_avoidance_grid
        ```

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

        Example:
        ```py
        import numpy as np

        air_grid: np.ndarray = self.mediator.get_air_grid
        ```

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

        Example:
        ```py
        import numpy as np

        air_vs_ground_grid: np.ndarray = (
            self.mediator.get_air_vs_ground_grid
        )
        ```

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

        Example:
        ```py
        import numpy as np

        cached_ground_grid: np.ndarray = (
            self.mediator.get_cached_ground_grid
        )
        ```

        Returns
        -------
        np.ndarray :
            The clean ground pathing grid.

        """
        return self.manager_request(
            ManagerName.PATH_MANAGER, ManagerRequestType.GET_CACHED_GROUND_GRID
        )

    @property
    def get_climber_grid(self) -> np.ndarray:
        """Get the climber ground pathing grid for reapers and colossus.

        PathManager

        Example:
        ```py
        import numpy as np

        climber_grid: np.ndarray = (
            self.mediator.get_climber_grid
        )
        ```

        Returns
        -------
        np.ndarray :
            The climber pathing grid.

        """
        return self.manager_request(
            ManagerName.PATH_MANAGER, ManagerRequestType.GET_CLIMBER_GRID
        )

    @property
    def get_forcefield_positions(self) -> List[Point2]:
        """Get positions of forcefields.

        PathManager

        Example:
        ```py
        from sc2.position import Point2

        ff_positions: list[Point2] = self.mediator.get_forcefield_positions
        ```

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
    def get_ground_to_air_grid(self) -> np.ndarray:
        """Get the ground pathing grid.

        PathManager

        Returns
        -------
        np.ndarray :
            The ground pathing grid.

        """
        return self.manager_request(
            ManagerName.PATH_MANAGER, ManagerRequestType.GET_GROUND_TO_AIR_GRID
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

        Parameters
        ----------
        grid : np.ndarray
            The grid to evaluate safety on.
        position : Point2
            The position to check the safety of.
        weight_safety_limit : float
            The maximum value the point can have on the grid to be considered safe.

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

        Parameters
        ----------
        position : Point2
            The intended building position.
        structure_type : UnitID
            Structure type we want to place.
        include_addon : bool, optional
            For Terran structures, check addon will place too.

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

    @property
    def get_placements_dict(self, **kwargs) -> dict:
        """Get the placement dict ares calculated at beginning
        of the game.

        Structure of dictionary:

        base_loc is a Point2 key for every expansion location on map.

        ```
        placement_dict = {
            base_loc: Point2:
                BuildingSize.TWO_BY_TWO: {
                    building_pos: Point2((2, 2)):
                        {
                            available: True,
                            has_addon: False
                            taken: False,
                            is_wall: True,
                            building_tag: 0,
                            worker_on_route: False,
                            time_requested: 0.0,
                            production_pylon: False,
                            bunker: False,
                            optimal_pylon: False
                        },
                        {...}
                },
                BuildingSize.THREE_BY_THREE: {
                    building_pos: Point2((5, 5)):
                        {
                            available: True,
                            has_addon: False
                            taken: False,
                            is_wall: True,
                            building_tag: 0,
                            worker_on_route: False,
                            time_requested: 0.0,
                            production_pylon: False,
                            bunker: False,
                            optimal_pylon: False
                        },
                        {...}
                },
            {...}
        }
        ```

        PlacementManager


        Returns
        ----------
        dict :
            Indicating if structure can be placed at given position.
        """
        return self.manager_request(
            ManagerName.PLACEMENT_MANAGER, ManagerRequestType.GET_PLACEMENTS_DICT
        )

    def request_building_placement(self, **kwargs) -> Optional[Point2]:
        """Request a building placement from the precalculated building formation.

        PlacementManager

        Parameters
        ----------
        base_location : Point2
            The general area where the placement should be near.
            This should be a expansion location.
        structure_type : UnitID
            Structure type requested.
        wall : bool, optional
            Request a wall structure placement.
            Will find alternative if no wall placements available.
        find_alternative : bool, optional (NOT YET IMPLEMENTED)
            If no placements available at base_location, find
            alternative at nearby base.
        reserve_placement : bool, optional
            Reserve this booking for a while, so another customer doesnt
            request it.
        within_psionic_matrix : bool, optional
            Protoss specific -> calculated position have power?
        closest_to : Optional[Point2]

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

    def request_warp_in(self, **kwargs) -> None:
        """Request a warp in spot, without making a query to the game client.

        PlacementManager

        Parameters
        ----------
        unit_type: UnitTypeId
            The unit we want to warp in
        target : Optional[Point2]
            If provided, attempt to find spot closest to this
            location.
        """
        return self.manager_request(
            ManagerName.PLACEMENT_MANAGER,
            ManagerRequestType.REQUEST_WARP_IN,
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

        Parameters
        ----------
        worker_tag : int
            Tag of the worker to be removed.

        Returns
        ----------
        None
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

        Parameters
        ----------
        target_position : Point2
            Location to get the closest workers to.
        force_close : bool
            Select the available worker closest to `target_position` if True.
        select_persistent_builder : bool
            If True we can select the persistent_builder if it's available.
        only_select_persistent_builder : bool
            If True, don't find an alternative worker
        min_health_perc :
            Only select workers above this health percentage.
        min_shield_perc :
            Only select workers above this shield percentage.

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

    """
    SquadManager
    """

    def get_position_of_main_squad(self, **kwargs) -> Point2:
        """Given a unit role, find where the main squad is.

        SquadManager

        Parameters
        ----------
        role : UnitRole
            Get the squads for this unit role.

        Returns
        -------
        Point2 :

        """
        return self.manager_request(
            ManagerName.SQUAD_MANAGER,
            ManagerRequestType.GET_POSITION_OF_MAIN_SQUAD,
            **kwargs,
        )

    def get_squads(self, **kwargs) -> list["UnitSquad"]:
        """Given a unit role, get the updated squads.

        SquadManager

        Parameters
        ----------
        role : UnitRole
            Get the squads for this unit role.
        squad_radius : float (default = 11.0)
            The threshold as to which separate squads are formed.
        unit_type: Optional[Union[UnitID, set[UnitID]]] (default = None)
            If specified, only form squads with these unit types
            WARNING: Will not remove units that have already
                     been assigned to a squad.

        Returns
        -------
        List[UnitSquad] :
            Each squad with this unit role.

        """
        return self.manager_request(
            ManagerName.SQUAD_MANAGER,
            ManagerRequestType.GET_SQUADS,
            **kwargs,
        )

    def remove_tag_from_squads(self, **kwargs) -> None:
        """
        Squad Manager
        Keyword args:
            tag: int
        """
        return self.manager_request(
            ManagerName.SQUAD_MANAGER,
            ManagerRequestType.REMOVE_TAG_FROM_SQUADS,
            **kwargs,
        )

    """
    TerrainManager
    """

    def building_position_blocked_by_burrowed_unit(self, **kwargs) -> Optional[Point2]:
        """See if the building position is blocked by a burrowed unit.

        TerrainManager

        Parameters
        ----------
        worker_tag : int
            The worker attempting to build the structure.
        position : Point2
            Where the structure is attempting to be placed.

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

        Parameters
        ----------
        th_pos : Point2
            Position of townhall to find points behind the mineral line of.

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

        Parameters
        ----------
        from_pos : Point2
            Position the Overlord spot should be closest to.

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

        Parameters
        -----
        start_point : Point2
            Where to start the flood fill.
        max_dist : float
            Only include points closer than this distance to the start point.

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

    def get_own_unit_count(self, **kwargs) -> int:
        """Get the dictionary of own structure types to the units themselves.

        UnitCacheManager

        Parameters
        -----
        unit_type_id : UnitID
            Unit type to count.
        include_alias : bool
            Check aliases. (default=True)

        Returns
        -------
        int :
            Total count of this unit including aliases if specified.

        """
        return self.manager_request(
            ManagerName.UNIT_CACHE_MANAGER,
            ManagerRequestType.GET_OWN_UNIT_COUNT,
            **kwargs,
        )

    def get_units_from_tags(self, **kwargs) -> List[Unit]:
        """Get a `list` of `Unit` objects corresponding to the given tags.

        UnitCacheManager

        Parameters
        -----
        tags : Set[int]
            Tags of the units to retrieve.

        Returns
        ----------
        None
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

        Parameters
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

        Parameters
        -----
        tag : int
            Tag of the unit to be assigned.
        role : UnitRole
            What role the unit should have.
        remove_from_squad : bool (default = True)
            Attempt to remove this unit from squad bookkeeping.

        Returns
        ----------
        None
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

        Parameters
        -----
        tags : Set[int]
            Tags of the units to assign to a role.
        role : UnitRole
            The role the units should be assigned to.

        Returns
        ----------
        None
        """
        return self.manager_request(
            ManagerName.UNIT_ROLE_MANAGER,
            ManagerRequestType.BATCH_ASSIGN_ROLE,
            **kwargs,
        )

    def clear_role(self, **kwargs) -> None:
        """Clear a unit's role.

        UnitRoleManager

        Parameters
        -----
        tag : int
            Tag of the unit to clear the role of.

        Returns
        ----------
        None
        """
        return self.manager_request(
            ManagerName.UNIT_ROLE_MANAGER, ManagerRequestType.CLEAR_ROLE, **kwargs
        )

    def get_all_from_roles_except(self, **kwargs) -> Units:
        """Get all units from the given roles except for unit types in excluded.

        UnitRoleManager

        Parameters
        -----
        roles : Set[UnitRole]
            Roles to get units from.
        excluded : Set[UnitTypeId]
            Unit types that should not be included.

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

        Parameters
        ----------
        role : UnitRole
            Role to get units from.
        unit_type : UnitTypeId
            Type(s) of units that should be returned. If omitted, all units with the
            role will be returned.
        restrict_to : Set[UnitTypeId]
            If supplied, only take Units with the given role and type if they also exist
            here.

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

        Parameters
        -----
        roles : Set[UnitRole]
            Roles to get units from.
        unit_type : UnitTypeId
            Type(s) of units that should be returned. If omitted, all units with the
            role will be returned.

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

        Parameters
        ----------
        amount : int
            Num workers to assign to each gas building

        Returns
        ----------
        None
        """
        return self.manager_request(
            ManagerName.RESOURCE_MANAGER,
            ManagerRequestType.SET_WORKERS_PER_GAS,
            **kwargs,
        )

    def switch_roles(self, **kwargs) -> None:
        """Give all units in a role a different role.

        UnitRoleManager

        Parameters
        -----
        from_role : UnitRole
            Role the units currently have.
        to_role : UnitRole
            Role to assign to the units.

        Returns
        ----------
        None
        """
        return self.manager_request(
            ManagerName.UNIT_ROLE_MANAGER,
            ManagerRequestType.SWITCH_ROLES,
            **kwargs,
        )
