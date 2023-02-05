"""Cache armies for better and faster tracking.

"""
from collections import defaultdict
from typing import Any, DefaultDict, Dict, List, Optional, Set, Union

from sc2.game_data import AbilityData
from sc2.ids.unit_typeid import UnitTypeId as UnitID
from sc2.unit import Unit
from sc2.units import Units

from ..consts import (
    CREEP_TUMOR_TYPES,
    EGG_BUTTON_NAMES,
    UNITS_TO_IGNORE,
    WORKER_TYPES,
    ManagerName,
    ManagerRequestType,
)
from ..custom_bot_ai import CustomBotAI
from ..dicts.does_not_use_larva import DOES_NOT_USE_LARVA
from ..managers.manager import Manager
from ..managers.manager_mediator import IManagerMediator, ManagerMediator


class UnitCacheManager(Manager, IManagerMediator):
    """Manager for caching units."""

    def __init__(
        self,
        ai: CustomBotAI,
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
        self.enemy_army_dict: DefaultDict = defaultdict(Units([], ai))
        self.own_army_dict: DefaultDict = defaultdict(Units([], ai))
        # used for assigning roles to locusts, may not be useful
        self.old_own_army: DefaultDict = defaultdict(Units([], ai))
        self.own_structures_dict: DefaultDict = defaultdict(Units([], ai))
        self.own_structure_tags: Set = set()
        # keep track of units that get removed so they can be deleted from memory units
        self.removed_units: Units = Units([], ai)
        # keep track of unit tags we want to remove each step so we can do it in one
        # operation
        self.enemy_tags_to_remove: Set[int] = set()
        self.enemy_army_units_to_add: Units = Units([], ai)

    def manager_request(
        self,
        receiver: ManagerName,
        request: ManagerRequestType,
        reason: str = None,
        **kwargs
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
    def own_army_value(self) -> int:
        """Combined mineral and vespene cost of our own army.

        Returns
        -------
        int :
            Total resource value of our army.

        """
        value: int = 0
        for unit in self.own_army:
            if unit.type_id in WORKER_TYPES:
                continue
            if unit.type_id == UnitID.EGG:
                egg_building: AbilityData = unit.orders[0].ability
                if egg_building.button_name not in EGG_BUTTON_NAMES:
                    value += egg_building.cost.minerals + egg_building.cost.vespene
            else:
                unit_cost = self.ai.calculate_unit_value(unit.type_id)
                value += unit_cost.minerals + unit_cost.vespene
        return value

    @property
    def ready_army_value(self) -> int:
        """Combined mineral and vespene cost of our own army excluding units in eggs.

        Returns
        -------
        int :
            Total resource value of our army excluding units in eggs.

        """
        # this doesn't consider units in eggs
        value: int = 0
        for unit in self.own_army:
            if unit.type_id in {UnitID.DRONE, UnitID.PROBE, UnitID.SCV}:
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
            if delete_from_dict:
                try:
                    self.enemy_army_dict[enemy_unit.type_id].remove(enemy_unit)
                except ValueError:
                    pass

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
        if enemy not in self.enemy_army_dict[enemy.type_id]:
            # only store a siege tank once
            if enemy.type_id == UnitID.SIEGETANK:
                if enemy not in self.enemy_army_dict[UnitID.SIEGETANKSIEGED]:
                    self.enemy_army_dict[enemy.type_id].append(enemy)
            elif enemy.type_id == UnitID.SIEGETANKSIEGED:
                if enemy not in self.enemy_army_dict[UnitID.SIEGETANK]:
                    self.enemy_army_dict[enemy.type_id].append(enemy)
            else:
                self.enemy_army_dict[enemy.type_id].append(enemy)

        if enemy.type_id in WORKER_TYPES and enemy.tag not in self.enemy_worker_tags:
            self.enemy_workers.append(enemy)
            return

        if enemy.type_id in UNITS_TO_IGNORE or enemy.is_hallucination:
            return
        # we've seen this enemy before, but we might want to update our records
        # ZERG MORPHS (baneling for example) CARRY THE SAME TAG FROM
        # ZERGLING -> BANELINGCOCOON -> BANELING
        if enemy.tag in self.enemy_army_tags:
            # This first part handles units that have morphed from something
            if (
                enemy.type_id in DOES_NOT_USE_LARVA
                or enemy.type_id == UnitID.HELLIONTANK
            ):
                enemy_unit: Optional[Unit] = self.ai.unit_tag_dict.get(enemy.tag, None)
                if enemy_unit:
                    self.enemy_tags_to_remove.add(enemy_unit.tag)
                    self.removed_units.append(enemy_unit)
                # we want this unit appended no matter what (we might not have seen the
                # original ling for example)
                self.enemy_army_units_to_add.append(enemy_unit)
            # we've seen this unit before, but want to update our records
            else:
                self.enemy_tags_to_remove.add(enemy.tag)
                self.enemy_army_units_to_add.append(enemy)

        # we've never seen this unit before, we can add it without worrying
        else:
            self.enemy_army.append(enemy)

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
        self.own_army_dict[unit.type_id].append(unit)
        if unit.type_id in UNITS_TO_IGNORE:
            return
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
        if unit.type_id not in CREEP_TUMOR_TYPES:
            self.own_structure_tags.add(unit.tag)
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
