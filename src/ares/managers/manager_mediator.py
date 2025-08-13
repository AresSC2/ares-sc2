"""Enable cross manager communication."""
from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    DefaultDict,
    Dict,
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
        **kwargs,
    ) -> Any:
        """How requests will be structured.

        Parameters:
            receiver: The Manager the request is being sent to.
            request: The Manager that made the request.
            reason: Why the Manager has made the request.
            kwargs: If the ManagerRequest is calling a function,
                that function's keyword arguments go here.

        Returns:
            Could be anything!
            Check docs for individual mediator requests for more info.


        """
        pass


class ManagerMediator(IManagerMediator):
    """
    Mediator concrete class is the single source of truth and coordinator of
    communications between the managers.
    """

    def __init__(self) -> None:
        self.managers: Dict[str, "Manager"] = {}  # noqa

    def add_managers(self, managers: list["Manager"]) -> None:  # noqa
        """Generate manager dictionary.

        Parameters:
            managers: List of all Managers capable of handling ManagerRequests.
        """
        for manager in managers:
            self.managers[str(type(manager).__name__)] = manager

    def manager_request(
        self,
        receiver: ManagerName,
        request: ManagerRequestType,
        reason: str = None,
        **kwargs,
    ) -> Any:
        """Function to request information from a manager.

        Parameters:
            receiver: Manager receiving the request.
            request: Requested attribute/function call.
            reason: Why the request is being made.
            kwargs: Keyword arguments (if any) to be passed to the requested function.

        Returns:
            Any: There are too many possible return types to list all of them.


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

        Returns:
            Unit tag to abilities and the next frame they can be casted.

        """
        return self.manager_request(
            ManagerName.ABILITY_TRACKER_MANAGER,
            ManagerRequestType.GET_UNIT_TO_ABILITY_DICT,
        )

    def update_unit_to_ability_dict(self, **kwargs) -> None:
        """Update tracking to reflect ability usage.

        After a unit uses an ability it should call this to update the frame the
        ability will next be available

        AbilityTrackerManager.

        Parameters:
            ability (AbilityId): The AbilityId that was used.
            unit_tag (int): The tag of the Unit that used the ability.

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

        Parameters:
            worker (Unit): The chosen worker.
            structure_type (UnitTypeId): What type of structure to build.
            pos (Point2): Where the structure should be placed.
            building_purpose (BuildingPurpose): Why the structure is being placed.

        Returns:
            bool: True if a position for the building is found and
            the worker is valid, otherwise False.



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

        Parameters:
            structure (Unit): The actual structure to cancel.

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

        Returns:
            DefaultDict[UnitTypeId, int]:
                Number of each type of UnitTypeId
                currently being tracked for building.
        """
        return self.manager_request(
            ManagerName.BUILDING_MANAGER, ManagerRequestType.GET_BUILDING_COUNTER
        )

    @property
    def get_building_tracker_dict(
        self,
    ) -> dict[int, dict[str, Union[Point2, Unit, UnitID, float]]]:
        """Get the building tracker dictionary.

        Building Manager.

        Returns:
            dict[int, dict[str, Union[Point2, Unit, UnitTypeId, float]]]:
                Tracks the worker tag to details such as the UnitTypeId of the
                building, the Point2 location for placement, the in-game
                time when the order started, and the purpose of the building.
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

        Parameters:
            own_units (Units): Our units involved in the battle.
            enemy_units (Units): The enemy units.
            timing_adjust (bool): Whether to consider the distance between units.
            good_positioning (bool): Whether to assume units are decently split.
            workers_do_no_damage (bool): Whether to ignore workers' damage.

        Returns:
            Enum indicating the human-readable engagement result.


        """
        return self.manager_request(
            ManagerName.COMBAT_SIM_MANAGER, ManagerRequestType.CAN_WIN_FIGHT, **kwargs
        )

    """
    CreepManager
    """

    def find_nearby_creep_edge_position(self, **kwargs) -> Point2 | None:
        """
        Find the nearest position on the edge of the creep nearby a given point.

        This function is used to determine a position that lies at the edge of the
        creep, in proximity to a reference point within a game map scenario. The edge
        of the creep refers to the boundary or border of an area covered by creep,
        a terrain-modifying biome commonly associated with certain game mechanics.

        Parameters
        ----------
        position : Point2
            Where to search from
        search_radius: float
            How far to search for creep edge position.
        closest_valid: bool
            If True find the closest valid edge tile from `position`.
            Else find the furthest
            Default is True.
        spread_dist: float
            How much distance between existing tumors?
            Default is 4.0

        Returns
        -------
        Point2 | None
            The coordinates of the nearest position at the edge of the creep.

        """
        return self.manager_request(
            ManagerName.CREEP_MANAGER,
            ManagerRequestType.FIND_NEARBY_CREEP_EDGE_POSITION,
            **kwargs,
        )

    def get_closest_creep_tile(self, **kwargs) -> None | Point2:
        """Get closest creep tile to `pos`

        WARNING: May return `None` if no creep tiles observed.

        CreepManager

        Example:
        ```py
        import numpy as np

        closest_tile: Point2 = (
            self.mediator.get_closest_creep_tile(pos=point)
        )
        ```

        Parameters:
            pos (Point2): The position to search for closest creep tile.

        Returns:
            Point2 representing the closest creep tile or None if no creep tiles.
        """
        return self.manager_request(
            ManagerName.CREEP_MANAGER,
            ManagerRequestType.GET_CLOSEST_CREEP_TILE,
            **kwargs,
        )

    @property
    def get_creep_coverage(self) -> float:
        """
        How much of the map is covered by creep?

        CreepManager

        Returns:
            A float between 0.0 and 100.0 indicating the coverage of the map.

        """
        return self.manager_request(
            ManagerName.CREEP_MANAGER, ManagerRequestType.GET_CREEP_COVERAGE
        )

    @property
    def get_creep_edges(self) -> tuple[np.ndarray, np.ndarray]:
        """
        Fetches the edges of the detected creep on the map.

        CreepManager

        The returned value represents
        the creep edges in the form of NumPy arrays.

        Returns:
            tuple of numpy.ndarray
                A tuple containing two NumPy arrays.
                Reflecting the coordinates of the creep edges.

        """
        return self.manager_request(
            ManagerName.CREEP_MANAGER, ManagerRequestType.GET_CREEP_EDGES
        )

    @property
    def get_creep_grid(self) -> np.ndarray:
        """Get the creep grid.
        Creep tiles have a value of 1.0
        Non creep tiles have any other value.

        CreepManager

        Example:
        ```py
        import numpy as np

        creep_grid: np.ndarray = (
            self.mediator.get_creep_grid
        )
        ```

        Returns:
            The creep grid.
        """
        return self.manager_request(
            ManagerName.CREEP_MANAGER, ManagerRequestType.GET_CREEP_GRID
        )

    @property
    def get_creep_tiles(self) -> np.ndarray:
        """Get creep tiles.

        CreepManager

        Example:
        ```py
        import numpy as np

        creep_tiles: np.ndarray = (
            self.mediator.get_creep_tiles
        )
        ```

        Returns:
            Coordinates of all creep tiles on the map.
        """
        return self.manager_request(
            ManagerName.CREEP_MANAGER, ManagerRequestType.GET_CREEP_TILES
        )

    def get_next_tumor_on_path(self, **kwargs) -> Point2 | None:
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

        return self.manager_request(
            ManagerName.CREEP_MANAGER,
            ManagerRequestType.GET_NEXT_TUMOR_ON_PATH,
            **kwargs,
        )

    def get_random_creep_position(self, **kwargs) -> Point2 | None:
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
        return self.manager_request(
            ManagerName.CREEP_MANAGER,
            ManagerRequestType.GET_RANDOM_CREEP_POSITION,
            **kwargs,
        )

    def get_overlord_creep_spotter_positions(self, **kwargs) -> dict[int, Point2]:
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
        return self.manager_request(
            ManagerName.CREEP_MANAGER,
            ManagerRequestType.GET_OVERLORD_CREEP_SPOTTER_POSTIONS,
            **kwargs,
        )

    def get_tumor_influence_lowest_cost_position(self, **kwargs) -> Point2 | None:
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
        return self.manager_request(
            ManagerName.CREEP_MANAGER,
            ManagerRequestType.GET_TUMOR_INFLUENCE_LOWEST_COST_POSITION,
            **kwargs,
        )

    """
    EnemyToBaseManager
    """

    @property
    def get_flying_enemy_near_bases(self) -> dict[int, set[int]]:
        """Get dictionary containing flying enemy near townhalls.

        EnemyToBase Manager

        Returns:
            dict[int, set[int]]:
                A dictionary mapping townhall tags (keys) to sets of
                 enemy tags (values) near each base.
        """
        return self.manager_request(
            ManagerName.ENEMY_TO_BASE_MANAGER,
            ManagerRequestType.GET_FLYING_ENEMY_NEAR_BASES,
        )

    @property
    def get_ground_enemy_near_bases(self, **kwargs) -> dict[int, set[int]]:
        """Get dictionary containing ground enemy near townhalls.

        EnemyToBase Manager

        Returns:
            dict[int, set[int]]:
                A dictionary where the integer key is a townhall tag.
                And the value contains a set of ints containing
                enemy tags near this base.
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

        Returns:
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

        Returns:
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

        Returns:
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
    def get_did_enemy_rush(self) -> bool:
        """
        Determines whether the enemy executed a rush strategy based
        on the intel manager's evaluation.

        WARNING: Super opinionated!

        Returns
        -------
        bool
            True if the enemy performed a rush strategy, otherwise False.
        """
        return self.manager_request(
            ManagerName.INTEL_MANAGER, ManagerRequestType.GET_DID_ENEMY_RUSH
        )

    @property
    def get_enemy_expanded(self) -> bool:
        """Has the enemy expanded?

        WARNING: Opinionated method, please write your own if you don't
        agree with this decision.

        Intel Manager

        Returns:
            Has enemy expanded out of their main?

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

        Returns:
            Is enemy four gate?

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

        Returns:
            Has enemy expanded out of natural?

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

        Returns:
            Enemy ling rushed?
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

        Returns:
            Enemy marine rushed?
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

        Returns:
            Enemy marauder rush?
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

        Returns:
            Enemy ravager rush?
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

        Returns:
            Enemy roach rushed?
        """
        return self.manager_request(
            ManagerName.INTEL_MANAGER, ManagerRequestType.GET_ENEMY_ROACH_RUSHED
        )

    @property
    def get_enemy_was_greedy(self) -> Point2:
        """Was the enemy greedy?

        WARNING: Currently not working, will always return `False`
        WARNING: Opinionated method, please write your own if you don't
        agree with this decision.

        Intel Manager

        Returns:
            Enemy was greedy?
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

        Returns:
            Enemy went four gate in this game?
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

        Returns:
            Enemy went marine rush in this game?
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

        Returns:
            Enemy went marauder rush in this game?

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

        Returns:
            Enemy went reaper in this game?
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

        Returns:
            Enemy went worker rush in this game?
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

        Returns:
            Enemy is attempting a proxy zealot rush?
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

        Returns:
            Key -> structure_tag, Value -> Information about the flight.
        """
        return self.manager_request(
            ManagerName.FLYING_STRUCTURE_MANAGER,
            ManagerRequestType.GET_FLYING_STRUCTURE_TRACKER,
        )

    def move_structure(self, **kwargs) -> None:
        """Request a structure to move via flight.

        FlyingStructureManager

        Parameters:
            structure (Unit): The structure to be moved or landed.
            target (Point2): The target location for the structure.
            should_land (bool, optional): Whether the structure should
                land after moving. Defaults to False.
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

        Returns:
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

        Returns:
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

        Returns:
            Dictionary where key is worker tag, and value is mineral tag.
        """
        return self.manager_request(
            ManagerName.RESOURCE_MANAGER,
            ManagerRequestType.GET_WORKER_TO_MINERAL_PATCH_DICT,
        )

    def remove_mineral_field(self, **kwargs) -> None:
        """Request for a mineral field to be removed from bookkeeping.

        Resource Manager

        Parameters:
            mineral_field_tag (int): The tag of the mineral patch to remove.
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

        Returns:
            Dictionary where key is worker tag, and value is gas building tag.
        """
        return self.manager_request(
            ManagerName.RESOURCE_MANAGER,
            ManagerRequestType.GET_WORKER_TO_GAS_BUILDING_DICT,
        )

    def remove_gas_building(self, **kwargs) -> None:
        """Request for a gas building to be removed from bookkeeping.

        Resource Manager

        Parameters:
            gas_building_tag (int): The tag of the gas building to remove.
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

        Parameters:
            from_pos (Point2): Where the search starts from.
            grid (np.ndarray): The grid to find the low-cost point on.
            radius (float): How far away the safe point can be.

        Returns:
            The closest location with the lowest cost.


        """
        return self.manager_request(
            ManagerName.PATH_MANAGER, ManagerRequestType.GET_CLOSEST_SAFE_SPOT, **kwargs
        )

    def find_low_priority_path(self, **kwargs) -> list[Point2]:
        """Find several points in a path.

        This way a unit can queue them up all at once for performance reasons.

        i.e. running drones from a base or sending an overlord to a new position.

        This does not return every point in the path. Instead, it returns points spread
        along the path.

        PathManager

        Parameters:
            start (Point2): Start point of the path.
            target (Point2): Desired end point of the path.
            grid (np.ndarray): The grid that should be used for pathing.

        Returns:
            List of points composing the path.
        """
        return self.manager_request(
            ManagerName.PATH_MANAGER,
            ManagerRequestType.FIND_LOW_PRIORITY_PATH,
            **kwargs,
        )

    def find_lowest_cost_points(self, **kwargs) -> list[Point2]:
        """Find the point(s) with the lowest cost within `radius` from `from_pos`.

        PathManager

        Parameters:
            from_pos (Point2): Point to start the search from.
            radius (float): How far away the returned points can be.
            grid (np.ndarray): Which grid to query for lowest cost points.

        Returns:
            Points with the lowest cost on the grid.
        """
        return self.manager_request(
            ManagerName.PATH_MANAGER,
            ManagerRequestType.FIND_LOWEST_COST_POINTS,
            **kwargs,
        )

    def find_path_next_point(self, **kwargs) -> Point2:
        """Find the next point in a path.

        Parameters:
            start (Point2): Start point of the path.
            target (Point2): Desired end point of the path.
            grid (np.ndarray): The grid that should be used for pathing.
            sensitivity (int, optional): Amount of points that should be
                skipped in the full path between tiles that are returned.
                Default value is 5.
            smoothing (bool, optional): Optional path smoothing where nodes are
                removed if it's possible to jump ahead some tiles in
                a straight line with a lower cost.
                Default value is False.
            sense_danger (bool, optional): Check to see if there are any
                dangerous tiles near the starting point. If this is True and
                there are no dangerous tiles near the starting point,
                the pathing query is skipped and the target is returned.
                Default value is True.
            danger_distance (float, optional): How far away from the
                start to look for danger.
                Default value is 20.
            danger_threshold (float, optional): Minimum value for a tile
                to be considered dangerous.
                Default value is 5.

        Returns:
            The next point in the path from the start to the target which may be the
            same as the target if it's safe.
        """
        return self.manager_request(
            ManagerName.PATH_MANAGER, ManagerRequestType.PATH_NEXT_POINT, **kwargs
        )

    def find_raw_path(self, **kwargs) -> list[Point2]:
        """Used for finding a full path, mostly for distance checks.

        PathManager

        Parameters:
            start (Point2): Start point of the path.
            target (Point2): Desired end point of the path.
            grid (np.ndarray): The grid that should be used for pathing.
            sensitivity (int): Amount of points that should be skipped in
                the full path between tiles that are returned.

        Returns:
            List of points composing the path.
        """
        return self.manager_request(
            ManagerName.PATH_MANAGER, ManagerRequestType.FIND_RAW_PATH, **kwargs
        )

    @property
    def get_air_avoidance_grid(self) -> np.ndarray:
        """Get the air avoidance pathing grid.
        Any tile with a value greater than one will contain some
        dangerous effects or spells that should always be avoided.
        Such as storms, nukes, ravager biles etc...

        GridManager

        Example:
        ```py
        import numpy as np

        avoidance_grid: np.ndarray = self.mediator.get_air_avoidance_grid
        ```

        Returns:
            The air avoidance pathing grid.

        """
        return self.manager_request(
            ManagerName.GRID_MANAGER, ManagerRequestType.GET_AIR_AVOIDANCE_GRID
        )

    @property
    def get_air_grid(self) -> np.ndarray:
        """Get the air pathing grid.

        Pathable tiles have a value of 1.0
        Pathable tiles with enemy influence have a value > 1.0
            The higher the value, the more influence there is.
        Non-pathable tiles have a value of np.inf

        GridManager

        Example:
        ```py
        import numpy as np

        air_grid: np.ndarray = self.mediator.get_air_grid
        ```

        Returns:
            The air pathing grid.
        """
        return self.manager_request(
            ManagerName.GRID_MANAGER, ManagerRequestType.GET_AIR_GRID
        )

    @property
    def get_air_vs_ground_grid(self) -> np.ndarray:
        """Get the air vs ground pathing grid. (air grid)

        grid is computed in a way that lowers the
        cost of nonpathable terrain for ground units,
        making air units naturally "drawn" to it.

        Pathable tiles have a value of 1.0
        Pathable tiles with enemy influence have a value > 1.0
            The higher the value, the more influence there is.
        Non-pathable tiles have a value of np.inf

        GridManager

        Example:
        ```py
        import numpy as np

        air_vs_ground_grid: np.ndarray = (
            self.mediator.get_air_vs_ground_grid
        )
        ```

        Returns:
            The air vs ground pathing grid.
        """
        return self.manager_request(
            ManagerName.GRID_MANAGER, ManagerRequestType.GET_AIR_VS_GROUND_GRID
        )

    @property
    def get_cached_ground_grid(self) -> np.ndarray:
        """Get a non-influence ground pathing grid.

        GridManager

        Example:
        ```py
        import numpy as np

        cached_ground_grid: np.ndarray = (
            self.mediator.get_cached_ground_grid
        )
        ```

        Returns:
            The clean ground pathing grid.
        """
        return self.manager_request(
            ManagerName.GRID_MANAGER, ManagerRequestType.GET_CACHED_GROUND_GRID
        )

    @property
    def get_climber_grid(self) -> np.ndarray:
        """Get the climber ground pathing grid for reapers and colossus.
        Pathable tiles have a value of 1.0
        Pathable tiles with enemy influence have a value > 1.0
            The higher the value, the more influence there is.
        Non-pathable tiles have a value of np.inf

        GridManager

        Example:
        ```py
        import numpy as np

        climber_grid: np.ndarray = (
            self.mediator.get_climber_grid
        )
        ```

        Returns:
            The climber pathing grid.
        """
        return self.manager_request(
            ManagerName.GRID_MANAGER, ManagerRequestType.GET_CLIMBER_GRID
        )

    @property
    def get_forcefield_positions(self) -> list[Point2]:
        """Get positions of forcefields.

        GridManager

        Example:
        ```py
        from sc2.position import Point2

        ff_positions: list[Point2] = self.mediator.get_forcefield_positions
        ```

        Returns:
            List of the center point of forcefields.

        """
        return self.manager_request(
            ManagerName.GRID_MANAGER,
            ManagerRequestType.GET_FORCEFIELD_POSITIONS,
        )

    @property
    def get_ground_avoidance_grid(self) -> np.ndarray:
        """Get the ground avoidance pathing grid.
        Any tile with a value greater than one will contain some
        dangerous effects or spells that should always be avoided.
        Such as storms, nukes, ravager biles etc...

        GridManager

        Returns:
            The ground avoidance pathing grid.

        """
        return self.manager_request(
            ManagerName.GRID_MANAGER, ManagerRequestType.GET_GROUND_AVOIDANCE_GRID
        )

    @property
    def get_ground_grid(self) -> np.ndarray:
        """Get the ground pathing grid.
        Pathable tiles have a value of 1.0
        Pathable tiles with enemy influence have a value > 1.0
            The higher the value, the more influence there is.
        Non-pathable tiles have a value of np.inf

        GridManager

        Returns:
            The ground pathing grid.
        """
        return self.manager_request(
            ManagerName.GRID_MANAGER, ManagerRequestType.GET_GROUND_GRID
        )

    @property
    def get_ground_to_air_grid(self) -> np.ndarray:
        """Get an air grid that contains influence for ground dangers
        that can shoot air.
        This can be useful for keeping air units safe that can't
        attack ground units.

        Pathable tiles have a value of 1.0
        Pathable tiles with enemy influence have a value > 1.0
            The higher the value, the more influence there is.
        Non-pathable tiles have a value of np.inf

        GridManager

        Returns:
            The ground pathing grid.
        """
        return self.manager_request(
            ManagerName.GRID_MANAGER, ManagerRequestType.GET_GROUND_TO_AIR_GRID
        )

    @property
    def get_map_data_object(self) -> MapData:
        """Get the MapAnalyzer.MapData object being used.

        PathManager

        Returns:
            The MapAnalyzer.MapData object being used.
        """
        return self.manager_request(
            ManagerName.GRID_MANAGER, ManagerRequestType.GET_MAP_DATA
        )

    @property
    def get_priority_ground_avoidance_grid(self) -> np.ndarray:
        """Get the pathing grid containing things ground units should always avoid.

        GridManager

        Returns:
            The priority ground avoidance pathing grid.
        """
        return self.manager_request(
            ManagerName.GRID_MANAGER,
            ManagerRequestType.GET_PRIORITY_GROUND_AVOIDANCE_GRID,
        )

    @property
    def get_tactical_ground_grid(self) -> np.ndarray:
        """Get the tactical ground grid.

        Normal pathable tiles with no units on them
        have a value of 200.0

        Tiles with more enemy have value > 200.0
        Tiles with more friendly have value < 200.0


        GridManager

        Returns:
            The ground tactical grid.
        """
        return self.manager_request(
            ManagerName.GRID_MANAGER, ManagerRequestType.GET_TACTICAL_GROUND_GRID
        )

    @property
    def get_whole_map_array(self) -> list[list[int]]:
        """Get the list containing every point on the map.

        GridManager

        Notes
        -----
        This does not return Point2s.

        Returns:
            Every point on the map.

        """
        return self.manager_request(
            ManagerName.PATH_MANAGER, ManagerRequestType.GET_WHOLE_MAP_ARRAY
        )

    @property
    def get_whole_map_tree(self) -> KDTree:
        """Get the KDTree of all points on the map.

        PathManager

        Returns:
            KDTree of all points on the map.
        """
        return self.manager_request(
            ManagerName.PATH_MANAGER, ManagerRequestType.GET_WHOLE_MAP_TREE
        )

    def is_position_safe(self, **kwargs) -> bool:
        """Check if the given position is considered dangerous.

        PathManager

        Parameters:
            grid (np.ndarray): The grid to evaluate safety on.
            position (Point2): The position to check the safety of.
            weight_safety_limit (float): The maximum value the point can
                have on the grid to be considered safe.
                Default value is 1.0.

        Returns:
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

        Parameters:
            position (Point2): The intended building position.
            structure_type (UnitID): Structure type we want to place.
            include_addon (bool, optional): For Terran structures,
                check addon will place too.

        Returns:
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

        Returns:
            Indicating if structure can be placed at given position.
        """
        return self.manager_request(
            ManagerName.PLACEMENT_MANAGER, ManagerRequestType.GET_PLACEMENTS_DICT
        )

    @property
    def get_pvz_nat_gatekeeping_pos(self, **kwargs) -> Union[Point2, None]:
        """Get the gatekeeper position in a PvZ natural wall if available.

        WARNING: This can return `None` so your code should account for this.

        PlacementManager


        Returns:
            Position of gatekeeper in natural wall
        """
        return self.manager_request(
            ManagerName.PLACEMENT_MANAGER, ManagerRequestType.GET_PVZ_NAT_GATEKEEPER_POS
        )

    def request_building_placement(self, **kwargs) -> Optional[Point2]:
        """Request a building placement from the precalculated building formation.

        PlacementManager

        Parameters:
            base_location (Point2): The general area where the placement should be near.
                This should be an expansion location.
            structure_type (UnitID): Structure type requested.
            first_pylon (bool, optional): Try to take designated
                first pylon if available.
                Default value is False.
            static_defence (bool, optional): Try to take designated
                static defence placements if available.
                Default value is False.
            wall (bool, optional): Request a wall structure placement.
                Will find alternative if no wall placements available.
                Default value is False.
            find_alternative (bool, optional): If no placements available
                at base_location, find an alternative at a nearby base.
                Default value is True.
            reserve_placement (bool, optional): Reserve this booking for a
                while, so another customer doesn't request it.
                Default value is True.
            within_psionic_matrix (bool, optional): Protoss specific -> calculated
                position have power?
                Default value is False.
            pylon_build_progress (float, optional): Only relevant
                if `within_psionic_matrix = True`.
                Default value is 1.0.
            closest_to (Point2, optional): Find placement at base closest to this.


        Returns:
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

        Parameters:
            unit_type (UnitTypeId): The unit we want to warp in.
            target (Optional[Point2]): If provided, attempt to find
                spot closest to this location.
        """
        return self.manager_request(
            ManagerName.WARP_IN_MANAGER,
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

        Returns:
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

        Parameters:
            worker_tag: Tag of the worker to be removed.
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

        Parameters:
            target_position (Point2): Location to get the closest workers to.
            force_close (bool): Select the available worker closest to
                `target_position` if True.
            select_persistent_builder (bool): If True, we can select
                the persistent_builder if it's available.
            only_select_persistent_builder (bool): If True, don't find an
                alternative worker.
            min_health_perc (float): Only select workers above this health percentage.
            min_shield_perc (float): Only select workers above this shield percentage.

        Returns:
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

        Returns:
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

        Parameters:
            role (UnitRole): Get the squads for this unit role.

        Returns:
            Position of main squad for this `role`
        """
        return self.manager_request(
            ManagerName.SQUAD_MANAGER,
            ManagerRequestType.GET_POSITION_OF_MAIN_SQUAD,
            **kwargs,
        )

    def get_squads(self, **kwargs) -> list["UnitSquad"]:
        """Given a unit role, get the updated squads.

        SquadManager

        Parameters:
            role (UnitRole): Get the squads for this unit role.
            squad_radius: The threshold as to which separate squads are formed.
            unit_type: If specified, only form squads with these unit types
                WARNING: Will not remove units that have already
                         been assigned to a squad.

        Returns:
            Each squad with this unit role.
        """
        return self.manager_request(
            ManagerName.SQUAD_MANAGER,
            ManagerRequestType.GET_SQUADS,
            **kwargs,
        )

    def remove_tag_from_squads(self, **kwargs) -> None:
        """
        SquadManager

        Parameters:
            tag (int): Get the squads for this unit role.
            squad_radius (float): The threshold as to which separate squads are formed.
            unit_type (UnitTypeId): If specified, only form squads with these unit types
                WARNING: Will not remove units that have already
                         been assigned to a squad.

        Returns:
            Each squad with this unit role.
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

        Parameters:
            worker_tag (int): The worker attempting to build the structure.
            position (Point2): Where the structure is attempting to be placed.

        Returns:
            The position that's blocked by an enemy unit.
        """
        return self.manager_request(
            ManagerName.TERRAIN_MANAGER,
            ManagerRequestType.BUILDING_POSITION_BLOCKED_BY_BURROWED_UNIT,
            **kwargs,
        )

    def get_behind_mineral_positions(self, **kwargs) -> list[Point2]:
        """Finds 3 spots behind the mineral line

        This is useful for building structures out of typical cannon range.

        TerrainManager

        Parameters:
            th_pos (Point2): Position of townhall to find points behind
                the mineral line of.

        Returns:
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

        Parameters:
            from_pos (Point2): Position the Overlord spot should be closest to.

        Returns:
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

        Returns:
            Location of the third base furthest from the enemy.

        """
        return self.manager_request(
            ManagerName.TERRAIN_MANAGER, ManagerRequestType.GET_DEFENSIVE_THIRD
        )

    @property
    def get_enemy_expansions(self) -> list[Tuple[Point2, float]]:
        """Get the expansions, as ordered from the enemy's point of view.

        TerrainManager

        Returns:
            list[Tuple[Point2, float]]:
                The first element is the
                location of the base. The second element is the pathing
                distance from the enemy main base.
        """
        return self.manager_request(
            ManagerName.TERRAIN_MANAGER, ManagerRequestType.GET_ENEMY_EXPANSIONS
        )

    @property
    def get_enemy_fourth(self) -> Point2:
        """Get the enemy fourth base.

        TerrainManager

        Returns:
            Location of the enemy fourth base.
        """
        return self.manager_request(
            ManagerName.TERRAIN_MANAGER, ManagerRequestType.GET_ENEMY_FOURTH
        )

    @property
    def get_enemy_nat(self) -> Point2:
        """Get the enemy natural expansion.

        TerrainManager

        Returns:
            Location of the enemy natural expansion.

        """
        return self.manager_request(
            ManagerName.TERRAIN_MANAGER, ManagerRequestType.GET_ENEMY_NAT
        )

    @property
    def get_enemy_ramp(self) -> Ramp:
        """Get the enemy main base ramp.

        TerrainManager

        Returns:
            sc2 Ramp object for the enemy main base ramp.
        """
        return self.manager_request(
            ManagerName.TERRAIN_MANAGER, ManagerRequestType.GET_ENEMY_RAMP
        )

    @property
    def get_enemy_third(self) -> Point2:
        """Get the enemy third base.

        TerrainManager

        Returns:
            Location of the enemy third base.

        """
        return self.manager_request(
            ManagerName.TERRAIN_MANAGER, ManagerRequestType.GET_ENEMY_THIRD
        )

    def get_flood_fill_area(self, **kwargs) -> set[tuple[int, int]]:
        """Given a point, flood fill outward from it and return the valid points.

        This flood fill does not continue through chokes.

        TerrainManager

        Parameters:
            start_point (Point2): Where to start the flood fill.
            max_dist (float): Only include points closer than this
                distance to the start point.

        Returns:
            Tuple[int, List[Tuple[int, int]]]:
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

        Returns:
            The pathing grid as it was on the first iteration.
        """
        return self.manager_request(
            ManagerName.TERRAIN_MANAGER, ManagerRequestType.GET_INITIAL_PATHING_GRID
        )

    @property
    def get_is_free_expansion(self) -> bool:
        """Check all bases for a free expansion.

        TerrainManager

        Returns:
            True if there exists a free expansion, False otherwise.
        """
        return self.manager_request(
            ManagerName.TERRAIN_MANAGER, ManagerRequestType.GET_IS_FREE_EXPANSION
        )

    @property
    def get_map_choke_points(self) -> set[Point2]:
        """All the points on the map that compose choke points.

        TerrainManager

        Returns:
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

        Returns:
            Overlord spot near the enemy natural.
        """
        return self.manager_request(
            ManagerName.TERRAIN_MANAGER,
            ManagerRequestType.GET_OL_SPOT_NEAR_ENEMY_NATURAL,
        )

    @property
    def get_ol_spots(self) -> list[Point2]:
        """High ground Overlord hiding spots.

        TerrainManager

        Returns:
            List of Overlord hiding spots.

        """
        return self.manager_request(
            ManagerName.TERRAIN_MANAGER,
            ManagerRequestType.GET_OL_SPOTS,
        )

    @property
    def get_own_expansions(self) -> list[Tuple[Point2, float]]:
        """Get the expansions.

        TerrainManager

        Returns:
            List[Tuple[Point2, float]]: List of Tuples where
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

        Returns:
            Location of our natural expansion.
        """
        return self.manager_request(
            ManagerName.TERRAIN_MANAGER, ManagerRequestType.GET_OWN_NAT
        )

    @property
    def get_positions_blocked_by_burrowed_enemy(self) -> list[Point2]:
        """Build positions that are blocked by a burrowed enemy unit.

        TerrainManager

        Returns:
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

        Returns:
            The enemy army.
        """
        return self.manager_request(
            ManagerName.UNIT_CACHE_MANAGER, ManagerRequestType.GET_CACHED_ENEMY_ARMY
        )

    @property
    def get_cached_enemy_workers(self) -> Units:
        """Get the Units object for the enemy workers.

        UnitCacheManager

        Returns:
            The enemy workers.
        """
        return self.manager_request(
            ManagerName.UNIT_CACHE_MANAGER, ManagerRequestType.GET_CACHED_ENEMY_WORKERS
        )

    @property
    def get_enemy_army_dict(self) -> DefaultDict[UnitID, Units]:
        """Get the dictionary of enemy army unit types to the units themselves.

        UnitCacheManager

        Returns:
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

        Returns:
            The dictionary of own army unit types to the units themselves.
        """
        return self.manager_request(
            ManagerName.UNIT_CACHE_MANAGER, ManagerRequestType.GET_OLD_OWN_ARMY_DICT
        )

    @property
    def get_own_army(self) -> Units:
        """Get the Units object for our own army.

        UnitCacheManager

        Returns:
            Our own army.
        """
        return self.manager_request(
            ManagerName.UNIT_CACHE_MANAGER, ManagerRequestType.GET_CACHED_OWN_ARMY
        )

    @property
    def get_own_army_dict(self) -> Dict[UnitID, Units]:
        """Get the dictionary of own army unit types to the units themselves.

        UnitCacheManager

        Returns:
            The dictionary of own army unit types to the units themselves.
        """
        return self.manager_request(
            ManagerName.UNIT_CACHE_MANAGER, ManagerRequestType.GET_CACHED_OWN_ARMY_DICT
        )

    @property
    def get_own_structures_dict(self) -> DefaultDict[UnitID, Units]:
        """Get the dictionary of own structure types to the units themselves.

        UnitCacheManager

        Returns:
            The dictionary of own structure types to the units themselves.
        """
        return self.manager_request(
            ManagerName.UNIT_CACHE_MANAGER, ManagerRequestType.GET_OWN_STRUCTURES_DICT
        )

    def get_own_unit_count(self, **kwargs) -> int:
        """Get the dictionary of own structure types to the units themselves.

        UnitCacheManager

        Parameters:
            unit_type_id (UnitID): Unit type to count.
            include_alias (bool): Check aliases. (default=True)

        Returns:
            Total count of this unit including aliases if specified.
        """
        return self.manager_request(
            ManagerName.UNIT_CACHE_MANAGER,
            ManagerRequestType.GET_OWN_UNIT_COUNT,
            **kwargs,
        )

    def get_units_from_tags(self, **kwargs) -> list[Unit]:
        """Get a `list` of `Unit` objects corresponding to the given tags.

        UnitCacheManager

        Parameters:
            tags: Tags of the units to retrieve.
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

        Returns:
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

        Returns:
            All enemy units.
        """
        return self.manager_request(
            ManagerName.UNIT_MEMORY_MANAGER, ManagerRequestType.GET_ALL_ENEMY
        )

    @property
    def get_enemy_ground(self) -> Units:
        """Get enemy ground units.

        UnitMemoryManager

        Returns:
            Enemy ground units.
        """
        return self.manager_request(
            ManagerName.UNIT_MEMORY_MANAGER, ManagerRequestType.GET_ENEMY_GROUND
        )

    @property
    def get_enemy_fliers(self) -> Units:
        """Get enemy flying units.

        UnitMemoryManager

        Returns:
            Enemy flying units.
        """
        return self.manager_request(
            ManagerName.UNIT_MEMORY_MANAGER, ManagerRequestType.GET_ENEMY_FLIERS
        )

    @property
    def get_enemy_tree(self) -> KDTree:
        """Get the KDTree representing all enemy unit positions.

        UnitMemoryManager

        Returns:
            KDTree representing all enemy unit positions.
        """
        return self.manager_request(
            ManagerName.UNIT_MEMORY_MANAGER, ManagerRequestType.GET_ENEMY_TREE
        )

    def get_units_in_range(
        self, **kwargs
    ) -> Union[Dict[Union[int, Tuple[float, float]], Units], list[Units]]:
        """Get units in range of other units or points.

        UnitMemoryManager

        Parameters:
            start_points (List[Union[Unit, Tuple[float, float]]]):
                List of `Unit`s or positions to search for units from.
            distances (Union[float, List[float]]): How far away from each point to
                query. Must broadcast to the length of `start_points`.
            query_tree (UnitTreeQueryType): Which KDTree should be queried.
            return_as_dict (bool, optional): Sets whether the returned units in range
                should be a dictionary or list. Default is False.


        Returns:
            Union[Dict[Union[int, Tuple[float, float]], Units], List[Units]]:
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

        Returns:
            KDTree representing all friendly unit positions.
        """
        return self.manager_request(
            ManagerName.UNIT_MEMORY_MANAGER, ManagerRequestType.GET_OWN_TREE
        )

    def get_is_detected(self, **kwargs) -> bool:
        """Get if the enemy currently is revealing a cloaked or burrowed unit.

        UnitMemoryManager

        Returns:
            Boolean if unit is detected.
        """
        return self.manager_request(
            ManagerName.UNIT_MEMORY_MANAGER,
            ManagerRequestType.GET_IS_DETECTED,
            **kwargs,
        )

    """
    UnitRoleManager
    """

    def assign_role(self, **kwargs) -> None:
        """Assign a unit a role.

        UnitRoleManager

        Parameters:
            tag (int): Tag of the unit to be assigned.
            role (UnitRole): What role the unit should have.
            remove_from_squad (bool, optional): Attempt to remove
                this unit from squad bookkeeping. Default is True.
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

        Parameters:
            tags (Set[int]): Tags of the units to assign to a role.
            role (UnitRole): The role the units should be assigned to.
        """
        return self.manager_request(
            ManagerName.UNIT_ROLE_MANAGER,
            ManagerRequestType.BATCH_ASSIGN_ROLE,
            **kwargs,
        )

    def clear_role(self, **kwargs) -> None:
        """Clear a unit's role.

        UnitRoleManager

        Parameters:
            tag (int): Tag of the unit to clear the role of.
        """
        return self.manager_request(
            ManagerName.UNIT_ROLE_MANAGER, ManagerRequestType.CLEAR_ROLE, **kwargs
        )

    def get_all_from_roles_except(self, **kwargs) -> Units:
        """Get all units from the given roles except for unit types in excluded.

        UnitRoleManager

        Parameters:
            roles (Set[UnitRole]): Roles to get units from.
            excluded (Set[UnitTypeId]): Unit types that should not be included.

        Returns:
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

        Returns:
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

        Parameters:
            role (UnitRole): Role to get units from.
            unit_type (UnitTypeId): Type(s) of units that should be returned.
                If omitted, all units with the role will be returned.
            restrict_to (Set[UnitTypeId]): If supplied, only take Units
                with the given role and type if they also exist here.

        Returns:
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

        Parameters:
            roles (Set[UnitRole]): Roles to get units from.
            unit_type (UnitTypeId): Type(s) of units that should be returned.
                If omitted, all units with the role will be returned.

        Returns:
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
        amount (int): Num workers to assign to each gas building
        """
        return self.manager_request(
            ManagerName.RESOURCE_MANAGER,
            ManagerRequestType.SET_WORKERS_PER_GAS,
            **kwargs,
        )

    def switch_roles(self, **kwargs) -> None:
        """Give all units in a role a different role.

        UnitRoleManager

        Parameters:
            from_role (UnitRole): Role the units currently have.
            to_role (UnitRole): Role to assign to the units.
        """
        return self.manager_request(
            ManagerName.UNIT_ROLE_MANAGER,
            ManagerRequestType.SWITCH_ROLES,
            **kwargs,
        )
