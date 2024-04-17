"""Manager for keeping track of enemy last known positions.

"""
from collections import deque
from typing import TYPE_CHECKING, Any, Deque, Dict, List, Optional, Tuple, Union

import numpy as np
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units
from scipy.spatial import KDTree

from ares.cache import property_cache_once_per_frame
from ares.consts import (
    BURROWED_ALIAS,
    IGNORED_UNIT_TYPES_MEMORY_MANAGER,
    MAX_SNAPSHOTS_PER_UNIT,
    ManagerName,
    ManagerRequestType,
    UnitTreeQueryType,
)
from ares.dicts.enemy_detector_ranges import DETECTOR_RANGES
from ares.managers.manager import Manager
from ares.managers.manager_mediator import IManagerMediator, ManagerMediator

if TYPE_CHECKING:
    from ares import AresBot


class UnitMemoryManager(Manager, IManagerMediator):
    """Keep track of enemy units.

    Structures are ignored.
    Based on MemoryManager from sharpy- thanks Infy/Merfolk
    """

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
            Bot object that will be running the game.
        config :
            Dictionary with the data from the configuration file
        mediator :
            ManagerMediator used for getting information from other managers.

        Returns
        -------

        """
        super(UnitMemoryManager, self).__init__(ai, config, mediator)
        self.manager_requests_dict = {
            ManagerRequestType.GET_ALL_ENEMY: lambda kwargs: self.all_enemies,
            ManagerRequestType.GET_ENEMY_GROUND: lambda kwargs: self.enemy_ground,
            ManagerRequestType.GET_ENEMY_FLIERS: lambda kwargs: self.enemy_fliers,
            ManagerRequestType.GET_ENEMY_TREE: lambda kwargs: self.enemy_tree,
            ManagerRequestType.GET_UNITS_IN_RANGE: lambda kwargs: self.units_in_range(
                **kwargs
            ),
            ManagerRequestType.GET_OWN_TREE: lambda kwargs: self.own_tree,
        }

        # Dictionary of units that we remember the position of. Keyed by unit tag.
        # Deque is used so that new snapshots are added to the left, and old ones are
        # removed from the right.
        self._memory_units_by_tag: Dict[int, Deque[Unit]] = {}

        # Dictionary of units that we know of, but which are longer present at the
        # location last seen. Keyed by unit tag
        self._archive_units_by_tag: Dict[int, Deque[Unit]] = {}
        self._tags_destroyed: set[int] = set()
        self.unit_dict: Dict[int, Deque[Unit]] = {}

        # remove units from memory after <time_in_seconds> based on air or ground
        self.expire_air: int = 30
        self.expire_ground: int = 30

        # tree stuff
        self.all_own: Units = self.ai.all_own_units
        self.all_enemies: Units = self.ai.all_enemy_units
        self.enemy_ground: Units = Units([], self.ai)
        self.enemy_fliers: Units = Units([], self.ai)
        self.enemy_tree: Optional[KDTree] = None
        self.own_tree: Optional[KDTree] = None
        self.enemy_ground_tree: Optional[KDTree] = None
        self.enemy_air_tree: Optional[KDTree] = None

        # empty units, so we don't have to generate it ten billion times
        self.empty_units: Units = Units([], self.ai)

    @property_cache_once_per_frame
    def enemy_detectors_and_ranges(
        self,
    ) -> Tuple[List[Union[Point2, List[float]]], List[float]]:
        """Cached unit positions and ranges for enemy detector.

        Returns
        -------
        Tuple[List[Union[Point2, List[float]]], List[float]] :
            First element is a `list` of detector positions.
            Second element is a `list` of detector ranges.

        """
        # get the positions and ranges
        enemy_detector_position: List[Union[Point2, List[float]]] = []
        enemy_detector_range: List[float] = []

        for effect in self.ai.state.effects:
            if effect.id in DETECTOR_RANGES:
                enemy_detector_position.append(list(effect.positions)[0])
                enemy_detector_range.append(DETECTOR_RANGES[effect.id])

        for unit in self.ai.enemy_detectors:
            enemy_detector_position.append(unit.position)
            enemy_detector_range.append(DETECTOR_RANGES[unit.type_id])

        return enemy_detector_position, enemy_detector_range

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
        """Update the manager to deal with memory units.

        Parameters
        ----------
        iteration :
            The game iteration.

        Returns
        -------

        """
        memory_tags_to_remove: List[int] = []
        detectors: Optional[Units] = None
        removed_unit_tags: set[int] = self.manager_mediator.manager_request(
            ManagerName.UNIT_CACHE_MANAGER, ManagerRequestType.GET_REMOVED_UNITS
        ).tags
        for unit_tag in self._memory_units_by_tag:
            # the unit_cache_manager removed the unit and we no longer want to track it
            if unit_tag in removed_unit_tags:
                memory_tags_to_remove.append(unit_tag)
                continue
            if self.is_unit_visible(unit_tag):
                continue

            snap = self.get_latest_snapshot(unit_tag)
            points: List[Point2] = [
                Point2((int(snap.position.x), int(snap.position.y))),
                Point2((int(snap.position.x + 1), int(snap.position.y))),
                Point2((int(snap.position.x), int(snap.position.y + 1))),
                Point2((int(snap.position.x + 1), int(snap.position.y + 1))),
            ]

            visible: bool = True

            for point in points:
                if not self.ai.is_visible(point):
                    visible = False
                    break

            expired: bool = self.check_expiration(snap)
            if expired:
                self.clear_unit_cache(memory_tags_to_remove, unit_tag)
            elif visible:
                # We see that the unit is no longer there.
                if (
                    snap.type_id in BURROWED_ALIAS or snap.is_burrowed
                ) and unit_tag not in self._tags_destroyed:
                    if detectors is None:
                        detectors = self.ai.all_own_units(detectors)

                    if detectors.closer_than(11, snap.position):
                        self.clear_unit_cache(memory_tags_to_remove, unit_tag)
                    else:
                        # change snapshot for burrowed units
                        # noinspection PyProtectedMember
                        snap._proto.is_burrowed = True
                else:
                    self.clear_unit_cache(memory_tags_to_remove, unit_tag)

        for tag in memory_tags_to_remove:
            self._memory_units_by_tag.pop(tag)

        memory_units = self.ghost_units

        # Merge enemy data with memories
        self.ai.enemy_units = self.ai.enemy_units + memory_units
        self.ai.all_enemy_units = self.ai.all_enemy_units + memory_units

        # generate tree information
        self.all_own = self.ai.all_own_units
        self.all_enemies = self.ai.all_enemy_units
        self.enemy_ground, self.enemy_fliers = self.ai.split_ground_fliers(
            self.all_enemies
        )
        self.generate_kd_trees()

    def clear_settings(self) -> None:
        """Reset lists and dicts.

        Called from _prepare_units.

        Returns
        -------

        """
        self.unit_dict.clear()

    def store_unit(self, unit: Unit) -> None:
        """Store unit in memory if necessary.

        Called from _prepare_units.

        Parameters
        ----------
        unit :
            Unit that may need to be stored.

        Returns
        -------

        """
        # Make sure each unit is only in one dictionary to avoid bugs
        assert not (
            unit.tag in self._memory_units_by_tag
            and unit.tag in self._archive_units_by_tag
        ), f"{unit} is in two dictionaries"

        # ignore ignored units and hallucinations
        if unit.type_id in IGNORED_UNIT_TYPES_MEMORY_MANAGER or unit.is_hallucination:
            return

        if unit.tag in self._archive_units_by_tag:
            snaps = self._archive_units_by_tag.pop(unit.tag)
        else:
            snaps = self._memory_units_by_tag.get(
                unit.tag, deque(maxlen=MAX_SNAPSHOTS_PER_UNIT)
            )

        snaps.appendleft(unit)

        if unit.tag not in self._memory_units_by_tag:
            self._memory_units_by_tag[unit.tag] = snaps

        self.unit_dict[unit.tag] = deque([unit])

    def is_unit_visible(self, unit_tag: int) -> bool:
        """Check if unit is visible.

        Parameters
        ----------
        unit_tag :
            Unit to check the visibility of.

        Returns
        -------
        bool :
            True if the unit is visible, False otherwise.

        """
        unit: Unit = self.ai.unit_tag_dict.get(unit_tag, None)
        return unit is not None and not unit.is_memory

    def get_latest_snapshot(self, unit_tag: int) -> Unit:
        """Returns the latest snapshot of a unit.

        Throws KeyError if unit_tag is not found.

        Parameters
        ----------
        unit_tag :
            Tag of the unit to get the most recent snapshot of.

        Returns
        -------
        Unit :
            Latest snapshot of the Unit with the given tag.

        """
        unit_deque = self._memory_units_by_tag[unit_tag]
        return unit_deque[0]

    @property
    def ghost_units(self) -> Units:
        """Latest snapshots of units that have been stored but are not visible.

        Notes
        -----
        Visibility here refers to whether the unit is included in the game observation,
        not cloak status.

        Returns
        -------
        Units :
            Units that have been stored but are not visible.

        """
        memory_units = Units([], self.ai)

        for tag in self._memory_units_by_tag:
            if self.is_unit_visible(tag):
                continue

            snap = self.get_latest_snapshot(tag)
            memory_units.append(snap)

        return memory_units

    def remove_unit(self, unit_tag: int) -> None:
        """Remove destroyed units from memory dictionaries.

        Parameters
        ----------
        unit_tag :
            Tag of the destroyed unit.

        Returns
        -------

        """
        self._memory_units_by_tag.pop(unit_tag, None)
        self._archive_units_by_tag.pop(unit_tag, None)

    def check_expiration(self, snap: Unit) -> bool:
        """Check if we need to remove the unit because it's been in memory for too long.

        Parameters
        ----------
        snap :
            Snapshot of the unit.

        Returns
        -------
        bool :
            True if the snapshot has expired and should be removed, False otherwise.

        """
        if snap.is_flying:
            return snap.age > self.expire_air
        return snap.age > self.expire_ground

    def clear_unit_cache(self, memory_tags_to_remove: List[int], unit_tag: int) -> None:
        """Clear the cache of the unit and archive it.

        Parameters
        ----------
        memory_tags_to_remove :
            Tags of units in memory that need to be removed.
        unit_tag :
            Tag of the unit to be archived.

        Returns
        -------

        """
        memory_tags_to_remove.append(unit_tag)
        snaps = self._memory_units_by_tag.get(unit_tag)
        self._archive_units_by_tag[unit_tag] = snaps

    def generate_kd_trees(self) -> None:
        """Generate cKDTrees using unit locations for quicker distance calculations.

        Returns
        -------

        """
        self.own_tree = self._create_tree(self.all_own)
        self.enemy_tree = self._create_tree(self.all_enemies)
        self.enemy_air_tree = self._create_tree(self.enemy_fliers)
        self.enemy_ground_tree = self._create_tree(self.enemy_ground)

    @staticmethod
    def _create_tree(units: Units) -> Optional[KDTree]:
        unit_position_list: List[List[float]] = [
            [unit.position.x, unit.position.y] for unit in units
        ]
        if unit_position_list:
            return KDTree(unit_position_list)
        else:
            return None

    def units_in_range(
        self,
        start_points: List[Union[Unit, Tuple[float, float]]],
        distances: Union[float, List[float]],
        query_tree: UnitTreeQueryType,
        return_as_dict: bool = False,
    ) -> Union[Dict[Union[Point2, int], Units], List[Units]]:
        """Get units within range of each `Unit` or `Point2` in `start_points`.

        Notes
        -----
        `distances` must broadcast to the length of `start_points`.

        Parameters
        ----------
        start_points: List[Union[Unit, Tuple[float, float]]]
            List of `Unit`s or positions to search for units from.
        distances: Union[float, List[float]]
            How far away from each point to query.
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
        tree, unit_container = self._get_tree_and_unit_container(query_tree)

        if tree is None:
            in_range_list = [self.empty_units for _ in range(len(start_points))]
        else:
            in_range_list: List[Units] = []
            if start_points:
                positions = [
                    u.position if isinstance(u, Unit) else u for u in start_points
                ]
                query_result = tree.query_ball_point(positions, distances)
                for result in query_result:
                    in_range_units = Units(
                        [unit_container[index] for index in result], self.ai
                    )
                    in_range_list.append(in_range_units)

        return (
            {
                start_points[idx].tag
                if isinstance(start_points[idx], Unit)
                else start_points[idx]: in_range_list[idx]
                for idx in range(len(start_points))
            }
            if return_as_dict
            else in_range_list
        )

    def _get_tree_and_unit_container(
        self, requested_query_type: UnitTreeQueryType
    ) -> Tuple[KDTree, Units]:
        """Get the trees and unit containers based on query type.

        Parameters
        ----------
        requested_query_type :
            Which tree needs to be queried.

        Returns
        -------
        Tuple[KDTree, Units] :
            First element is the KDTree to query.
            Second element is the units that make up that KDTree.

        """
        if requested_query_type == UnitTreeQueryType.AllEnemy:
            return self.enemy_tree, self.all_enemies
        elif requested_query_type == UnitTreeQueryType.EnemyFlying:
            return self.enemy_air_tree, self.enemy_fliers
        elif requested_query_type == UnitTreeQueryType.EnemyGround:
            return self.enemy_ground_tree, self.enemy_ground
        elif requested_query_type == UnitTreeQueryType.AllOwn:
            return self.own_tree, self.all_own
        else:
            raise ValueError(f"Unsupported query type: {requested_query_type}")

    def any_enemies_in_range(
        self, pos: Union[List[Point2], List[List[float]]], radius: float
    ) -> List[bool]:
        """Check if any enemies are in range of a list of points.

        Parameters
        ----------
        pos :
            Positions to check if there are enemy units in range of.
        radius :
            How far away from each point to check for enemy units.

        Returns
        -------
        List[bool] :
            True or False for each point in the list depending on if any enemy
            units are present within radius.

        """
        enemies_in_range = self.enemy_tree.query_ball_point(pos, radius)

        return [np.any(result) for result in enemies_in_range]

    def get_position_in_enemy_detector_range(self, position: Point2) -> bool:
        """Check if the given position is in range of an enemy detector.

        Parameters
        ----------
        position :
            The position to check.

        Returns
        -------
        bool :
            True if the position is within range of an enemy detector, False otherwise.

        """
        # get the positions and ranges
        enemy_detector_position, enemy_detector_range = self.enemy_detectors_and_ranges

        if not enemy_detector_position:
            # no detectors were found so no units are in range of detectors
            return False
        for i, pos in enumerate(enemy_detector_position):
            if position.distance_to(pos) < enemy_detector_range[i]:
                return True
        return False

    def get_own_units_in_enemy_detector_range(self) -> set[int]:
        """Find the tags of friendly units in range of an enemy detector.

        Given the recorded enemy detectors and effects, query all of our points in range
        of them. Doesn't take arguments as it's easier to query everything. This could
        be expanded later.

        Check for Revelation separately.

        Returns the

        Returns
        -------
        Set[int] :
            Set of tags of our units that are in range of a detector. This doesn't take
            our unit's radius into account, only the radius of the detector.

        """
        # skip if we don't have units
        if self.own_tree is None:
            return set()

        # need to get a set eventually, but lists are faster to add to
        unit_tags_in_range_list: List[int] = []

        # get the positions and ranges
        enemy_detector_position, enemy_detector_range = self.enemy_detectors_and_ranges

        if not enemy_detector_position:
            # no detectors were found so no units are in range of detectors
            return set()

        # run query
        units_in_ranges = self.own_tree.query_ball_point(
            enemy_detector_position, enemy_detector_range
        )
        for result in units_in_ranges:
            for idx in result:
                unit_tags_in_range_list.append(self.all_own[idx].tag)
        return set(unit_tags_in_range_list)
