"""Cache armies for better and faster tracking.

"""
from collections import defaultdict
from typing import TYPE_CHECKING, Any, Dict, List, Set, Union

from cython_extensions import cy_unit_pending
from sc2.data import Race
from sc2.game_data import AbilityData
from sc2.ids.unit_typeid import UnitTypeId as UnitID
from sc2.unit import Unit
from sc2.units import Units

from ares.cache import property_cache_once_per_frame
from ares.consts import (
    ALL_STRUCTURES,
    ALL_WORKER_TYPES,
    CREEP_TUMOR_TYPES,
    EGG_BUTTON_NAMES,
    TOWNHALL_TYPES,
    UNITS_TO_IGNORE,
    WORKER_TYPES,
    ManagerName,
    ManagerRequestType,
    UnitTreeQueryType,
)
from ares.dicts.does_not_use_larva import DOES_NOT_USE_LARVA
from ares.dicts.unit_alias import UNIT_ALIAS
from ares.managers.manager import Manager
from ares.managers.manager_mediator import IManagerMediator, ManagerMediator

if TYPE_CHECKING:
    from ares import AresBot


class UnitCacheManager(Manager, IManagerMediator):
    """Manager for caching units."""

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
            ManagerRequestType.GET_CACHED_ENEMY_ARMY: lambda kwargs: self.enemy_army,
            ManagerRequestType.GET_CACHED_ENEMY_ARMY_DICT: lambda kwargs: (
                self.enemy_army_dict
            ),
            ManagerRequestType.GET_CACHED_ENEMY_WORKERS: lambda kwargs: (
                self.enemy_workers
            ),
            ManagerRequestType.GET_OLD_OWN_ARMY_DICT: lambda kwargs: (
                self.old_own_army
            ),
            ManagerRequestType.GET_CACHED_OWN_ARMY: lambda kwargs: self.own_army,
            ManagerRequestType.GET_CACHED_OWN_ARMY_DICT: lambda kwargs: (
                self.own_army_dict
            ),
            ManagerRequestType.GET_OWN_STRUCTURES_DICT: lambda kwargs: (
                self.own_structures_dict
            ),
            ManagerRequestType.GET_OWN_UNIT_COUNT: lambda kwargs: (
                self.get_own_unit_count(**kwargs)
            ),
            ManagerRequestType.GET_UNITS_FROM_TAGS: lambda kwargs: (
                self.get_units_from_tags(**kwargs)
            ),
            ManagerRequestType.GET_REMOVED_UNITS: lambda kwargs: self.removed_units,
        }
        self.enemy_army: Units = Units([], ai)
        self.enemy_workers: Units = Units([], ai)
        self.own_army: Units = Units([], ai)
        self.enemy_army_tags: Set[int] = set()
        self.enemy_worker_tags: Set[int] = set()
        # keep a dict of units for fast lookup
        # caution: this is for bookkeeping only,
        # don't use distance checks here for example
        self.enemy_army_dict: defaultdict[UnitID, list] = defaultdict(list)
        self.own_army_dict: defaultdict[UnitID, list] = defaultdict(list)
        # used for assigning roles to locusts, may not be useful
        self.old_own_army: defaultdict[UnitID, list] = defaultdict(list)
        self.own_structures_dict: defaultdict[UnitID, list] = defaultdict(list)
        self.own_structure_tags: Set = set()
        # keep track of units that get removed, so they can be deleted from memory units
        self.removed_units: Units = Units([], ai)
        # keep track of unit tags we want to remove, so we can do it in one operation
        self.enemy_tags_to_remove: Set[int] = set()
        self.enemy_army_units_to_add: Units = Units([], ai)

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
        """Update unit caches.

        Parameters
        ----------
        iteration :
            The game iteration.

        Returns
        -------

        """
        self.removed_units: Units = Units([], self.ai)
        self.enemy_army_tags: Set[int] = self.enemy_army.tags
        self.enemy_worker_tags: Set[int] = self.enemy_workers.tags

    @property
    def enemy_army_value(self) -> int:
        """Combined mineral and vespene cost of the enemy army.

        Returns
        -------
        int :
            Total resource value of the enemy army.

        """
        value: int = 0
        for unit in self.enemy_army:
            if unit.type_id in WORKER_TYPES:
                continue
            unit_cost = self.ai.calculate_unit_value(unit.type_id)
            value += unit_cost.minerals + unit_cost.vespene
        return value

    @property
    def own_army_value(self, include_queens: bool = False) -> int:
        """Combined mineral and vespene cost of our own army.

        TODO: Add pending units for Terran and Protoss

        Returns
        -------
        int :
            Total resource value of our army.

        """
        value: int = 0
        for unit in self.own_army:
            type_id: UnitID = unit.type_id
            if type_id in ALL_WORKER_TYPES:
                continue
            if type_id == UnitID.EGG:
                egg_building: AbilityData = unit.orders[0].ability
                if egg_building.button_name not in EGG_BUTTON_NAMES:
                    value += egg_building.cost.minerals + egg_building.cost.vespene
            else:
                unit_cost = self.ai.calculate_unit_value(type_id)
                value += unit_cost.minerals + unit_cost.vespene

        # iterate through T/P structures and count pending units
        if self.ai.race != Race.Zerg:
            for s in self.ai.structures.filter(
                lambda _s: _s.orders
                and _s.is_ready
                and _s.type_id not in TOWNHALL_TYPES
            ):
                try:
                    order: UnitID = UnitID[s.orders[0].ability.button_name.upper()]
                    if order not in ALL_STRUCTURES:
                        unit_cost = self.ai.calculate_unit_value(order)
                        value += unit_cost.minerals + unit_cost.vespene
                except Exception:
                    pass

        # count queens if Z
        elif include_queens:
            value += 150 * len(
                [
                    th
                    for th in self.ai.townhalls
                    if th.orders
                    and th.orders[0].ability.button_name.upper() == UnitID.QUEEN.name
                ]
            )

        return value

    @property
    def ready_army_value(self) -> int:
        """Combined mineral and vespene cost of our own army excluding pending units.

        Returns
        -------
        int :
            Total resource value of our army excluding units in eggs.

        """
        # this doesn't consider units in eggs
        value: int = 0
        for unit in self.own_army:
            if unit.type_id in WORKER_TYPES:
                continue
            unit_cost = self.ai.calculate_unit_value(unit.type_id)
            value += unit_cost.minerals + unit_cost.vespene
        return value

    def remove_unit(self, unit_tag: int, delete_from_dict: bool = True) -> None:
        """Remove a unit from unit caches.

        Parameters
        ----------
        unit_tag :
            Tag of the unit to remove.
        delete_from_dict :
            Remove unit tag from `enemy_army_dict` if True.

        Returns
        -------

        """
        if unit_tag in self.ai._enemy_units_previous_map:
            enemy_unit = self.ai._enemy_units_previous_map[unit_tag]
            if unit_tag in self.enemy_army_tags:
                self.enemy_army.remove(enemy_unit)
            if unit_tag in self.enemy_worker_tags:
                self.enemy_workers.remove(enemy_unit)
            if (
                delete_from_dict
                and enemy_unit in self.enemy_army_dict[enemy_unit.type_id]
            ):
                self.enemy_army_dict[enemy_unit.type_id].remove(enemy_unit)

    def clear_store_dicts(self) -> None:
        """Clear dictionaries for storing units.

        Called from _prepare_units.

        Returns
        -------

        """
        self.old_own_army = self.own_army_dict.copy()
        self.own_army = Units([], self.ai)
        self.own_army_dict.clear()
        self.own_structures_dict.clear()

        self.enemy_tags_to_remove = set()
        self.enemy_army_units_to_add = Units([], self.ai)

    def store_enemy_unit(self, enemy: Unit) -> None:
        """Store enemy units.

        Called from _prepare_units.

        Parameters
        ----------
        enemy :
            Unit to store.

        Returns
        -------

        """
        enemy_army_dict: dict[UnitID, list] = self.enemy_army_dict
        tag: int = enemy.tag
        type_id: UnitID = enemy.type_id

        # we don't care about saving these
        if type_id in UNITS_TO_IGNORE or enemy.is_hallucination:
            return

        # never seen this unit before
        if tag not in self.enemy_army_tags:
            self.enemy_army.append(enemy)
            enemy_army_dict[enemy.type_id].append(enemy)

            if enemy.type_id in WORKER_TYPES and tag not in self.enemy_worker_tags:
                self.enemy_workers.append(enemy)
                return

        # we've seen this enemy before, but we might want to update our records
        # ZERG MORPHS (baneling for example) CARRY THE SAME TAG FROM
        # ZERGLING -> BANELINGCOCOON -> BANELING
        else:
            # This first part handles units that have morphed from something
            if type_id in DOES_NOT_USE_LARVA or type_id == UnitID.HELLIONTANK:
                if enemy_unit := self.ai.unit_tag_dict.get(tag, None):
                    self.enemy_tags_to_remove.add(tag)
                    self.removed_units.append(enemy_unit)
                # we want this unit appended no matter what (we might not have seen the
                # original ling for example)
                self.enemy_army_units_to_add.append(enemy_unit)
            # we've seen this unit before, but want to update our records
            else:
                self.enemy_tags_to_remove.add(tag)
                self.enemy_army_units_to_add.append(enemy)

    def update_enemy_army(self) -> None:
        """Update cached enemy army.

        All unit removal is done at the end so we can do it once in O(n) time.
        Called from `main.py`.

        Returns
        -------

        """
        # remove all enemy units this step
        self.enemy_army = Units(
            [
                unit
                for unit in self.enemy_army
                if unit.tag not in self.enemy_tags_to_remove
            ],
            self.ai,
        )
        # add fresh units
        self.enemy_army.extend(self.enemy_army_units_to_add)

    def store_own_unit(self, unit: Unit) -> None:
        """Store friendly unit.

        Called from _prepare_units.

        Parameters
        ----------
        unit :
            Unit to store.

        Returns
        -------

        """
        type_id: UnitID = unit.type_id
        self.own_army_dict[type_id].append(unit)
        if unit.type_id not in UNITS_TO_IGNORE:
            self.own_army.append(unit)

    def store_own_structure(self, unit: Unit) -> None:
        """Store friendly structure.

        Called from _prepare_units.

        Parameters
        ----------
        unit :
            Structure to store.

        Returns
        -------

        """
        type_id: UnitID = unit.type_id
        if type_id not in CREEP_TUMOR_TYPES:
            self.own_structure_tags.add(type_id)

        self.own_structures_dict[unit.type_id].append(unit)

    def get_units_from_tags(self, tags: Union[List[int], Set[int]]) -> List[Unit]:
        """Get a `list` of `Unit` objects corresponding to the given tags.

        Parameters
        ----------
        tags :
            Tags of the units to retrieve.

        Returns
        -------

        """
        retrieved_tags: List[Unit] = []
        for tag in tags:
            if tag in self.ai.unit_tag_dict:
                unit = self.ai.unit_tag_dict[tag]
                retrieved_tags.append(unit)
        return retrieved_tags

    @property_cache_once_per_frame
    def enemy_near_spawn(self) -> Units:
        """Get all enemy units within 60 of our main.

        Returns
        -------
        Units :
            Enemy units near our spawn.

        """
        return self.manager_mediator.get_units_in_range(
            start_positions=[self.ai.start_location],
            distances=60,
            query_type=UnitTreeQueryType.AllEnemy,
        )[0]

    def get_own_unit_count(
        self,
        unit_type_id: UnitID,
        include_alias: bool = True,
        include_pending: bool = True,
    ) -> int:
        """Get unit count, should include alias if specified.
        Includes pending units by default

        Examples:
        ```
        self.get_own_unit_count(UnitID.SIEGETANK, include_alias=True)
        Returns count for UnitID.SIEGETANK + UnitID.SIEGETANKSIEGED

        self.get_own_unit_count(UnitID.ZERGLING, include_alias=True)
        Returns count for UnitID.ZERGLING + UnitID.ZERGLINGBURROWED
        ```

        Parameters
        ----------
        unit_type_id :
            Tags of the units to retrieve.
        include_alias : default True
            Get other alias of this unit too (siegetank -> siegetanksieged).
        include_pending : default
            Count pending units.

        Returns
        -------
        int :
            Total number of unit_type_id.
        """
        army_dict: dict[UnitID, list[UnitID]] = self.own_army_dict

        num_units: int = len(army_dict[unit_type_id])

        if include_alias and unit_type_id in UNIT_ALIAS:
            num_units += len(army_dict[UNIT_ALIAS[unit_type_id]])

        if include_pending:
            num_units += cy_unit_pending(self.ai, unit_type_id)

        return num_units
