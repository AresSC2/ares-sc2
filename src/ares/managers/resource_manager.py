"""Anything to do with resource management and collection.

"""

import math
from collections import defaultdict
from typing import TYPE_CHECKING, Any, DefaultDict, Dict, List, Optional, Set

import numpy as np
from cython_extensions import (
    cy_closest_to,
    cy_distance_to_squared,
    cy_sorted_by_distance_to,
)
from sc2.data import Race
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units

from ares.cache import property_cache_once_per_frame
from ares.consts import (
    DEBUG,
    DEBUG_OPTIONS,
    IGNORED_UNIT_TYPES_MEMORY_MANAGER,
    MINERAL,
    RESOURCE_DEBUG,
    ManagerName,
    ManagerRequestType,
    UnitRole,
    UnitTreeQueryType,
)
from ares.managers.manager import Manager
from ares.managers.manager_mediator import IManagerMediator, ManagerMediator

if TYPE_CHECKING:
    from ares import AresBot


class ResourceManager(Manager, IManagerMediator):
    """Handles resource collection data structures."""

    MINING_RADIUS = 1.35
    grid: np.ndarray

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
        super(ResourceManager, self).__init__(ai, config, mediator)
        self.manager_requests_dict = {
            ManagerRequestType.GET_MINERAL_PATCH_TO_LIST_OF_WORKERS: lambda kwargs: (
                self.mineral_patch_to_list_of_workers
            ),
            ManagerRequestType.GET_MINERAL_TARGET_DICT: lambda kwargs: (
                self.mineral_target_dict
            ),
            ManagerRequestType.GET_NUM_AVAILABLE_MIN_PATCHES: lambda kwargs: (
                self.available_minerals.amount
            ),
            ManagerRequestType.GET_WORKER_TAG_TO_TOWNHALL_TAG: lambda kwargs: (
                self.worker_tag_to_townhall_tag
            ),
            ManagerRequestType.GET_WORKER_TO_GAS_BUILDING_DICT: lambda kwargs: (
                self.worker_to_geyser_dict
            ),
            ManagerRequestType.GET_WORKER_TO_MINERAL_PATCH_DICT: lambda kwargs: (
                self.worker_to_mineral_patch_dict
            ),
            ManagerRequestType.REMOVE_GAS_BUILDING: lambda kwargs: (
                self._remove_gas_building(**kwargs)
            ),
            ManagerRequestType.REMOVE_MINERAL_FIELD: lambda kwargs: (
                self._remove_mineral_field(**kwargs)
            ),
            ManagerRequestType.REMOVE_WORKER_FROM_MINERAL: lambda kwargs: (
                self.remove_worker_from_mineral(**kwargs)
            ),
            ManagerRequestType.SELECT_WORKER: lambda kwargs: (
                self.select_worker(**kwargs)
            ),
            ManagerRequestType.SET_WORKERS_PER_GAS: lambda kwargs: (
                self.set_worker_per_gas(**kwargs)
            ),
        }

        self.debug: bool = config[DEBUG]

        self.cached_townhalls: Units = Units([], self.ai)

        self.workers_per_gas: int = 3
        self.worker_to_mineral_patch_dict: Dict[int, int] = {}
        self.mineral_patch_to_list_of_workers: Dict[int, Set[int]] = {}

        self.worker_to_geyser_dict: Dict[int, int] = {}
        self.geyser_to_list_of_workers: Dict[int, Set[int]] = {}

        self.mineral_tag_to_mineral: Dict[int, Unit] = {}
        self.mineral_object_to_worker_units_object: DefaultDict[
            Unit, List[Unit]
        ] = defaultdict(list)
        # keep track of how many mineral patches we have available
        self.num_available_min_patches: int = 0
        # mineral targets are positions just before the mineral (for speed mining)
        self.mineral_target_dict: Dict[Point2, Point2] = {}
        # store which townhall the worker is closest to
        self.worker_tag_to_townhall_tag: Dict[int, int] = {}
        self._calculate_mineral_targets()

        self.went_one_base_defence: bool = False
        # For the initial split we have a special method to assign workers optimally
        self.initial_worker_split: bool = True

    def set_worker_per_gas(self, amount: int) -> None:
        """Sets how many workers to be assigned to each gas building

        Returns
        -------
        """
        self.workers_per_gas = amount

    @property_cache_once_per_frame
    def available_minerals(self) -> Units:
        """Find mineral fields near townhalls that have fewer than two assigned workers.

        Returns
        -------
        Units :
            Mineral fields near townhalls with fewer than two assigned workers.
        """
        available_minerals: Units = Units([], self.ai)
        progress: float = 0.85
        townhalls: Units = self.ai.townhalls.filter(
            lambda th: th.build_progress > progress
        )
        if not townhalls:
            return available_minerals

        for townhall in townhalls:
            if self.ai.mineral_field:
                # we want workers on closest mineral patch first
                minerals_sorted: list[Unit] = cy_sorted_by_distance_to(
                    self.ai.mineral_field.filter(
                        lambda mf: mf.is_visible
                        and not mf.is_snapshot
                        and mf.distance_to(townhall) < 10
                        and len(self.mineral_patch_to_list_of_workers.get(mf.tag, []))
                        < 2
                    ),
                    townhall.position,
                )

                if minerals_sorted:
                    available_minerals.extend(minerals_sorted)

        return available_minerals

    @property
    def safe_mineral_fields_at_townhalls(self) -> Units:
        """Find available patches that are safe.

        This is mostly to find patches for workers fleeing danger.

        Returns
        -------
        Units :
            Safe mineral patches.
        """
        units_near_patches: Dict[int, Units] = self.manager_mediator.get_units_in_range(
            start_points=self.available_minerals,
            distance=12,
            query_tree=UnitTreeQueryType.AllEnemy,
            return_as_dict=True,
        )
        return self.available_minerals.filter(
            lambda mf: units_near_patches[mf.tag]
            .filter(lambda u: u.tag not in IGNORED_UNIT_TYPES_MEMORY_MANAGER)
            .amount
            == 0
            # `self.available_minerals` checks this but that is cached per frame
            # so we might have already assigned workers since the frame started
            and len(self.mineral_patch_to_list_of_workers.get(mf.tag, [])) < 2
        )

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
        """Manage worker resource collection.

        Parameters
        ----------
        iteration :
            The game iteration.

        Returns
        -------

        """
        self.grid = self.manager_mediator.get_ground_grid
        if workers := self.manager_mediator.get_units_from_role(
            role=UnitRole.GATHERING
        ):
            if iteration % 4 == 0 or len(self.worker_to_mineral_patch_dict) == 0:
                self._assign_workers(workers)
                # keep memory of our townhalls, so we can deal with dead ths
                for th in self.ai.townhalls:
                    if th.tag not in self.cached_townhalls.tags and th.is_ready:
                        self.cached_townhalls.append(th)

            # TODO: this is here to fix a rare but, where a building worker is
            #   selected but somehow it remains in this manager's bookkeeping
            #   FIX THIS!
            if iteration % 32 == 0:
                for worker in workers:
                    if worker.tag in self.manager_mediator.get_building_tracker_dict:
                        self.remove_worker_from_mineral(worker.tag)
                        self.manager_mediator.assign_role(
                            tag=worker.tag, role=UnitRole.BUILDING
                        )

        if self.debug and self.config[DEBUG_OPTIONS][RESOURCE_DEBUG]:
            self._print_debug_information()

    def remove_worker_from_mineral(self, worker_tag: int) -> None:
        """Remove worker from internal data structures.

        This happens if worker gets assigned to do something else

        Parameters
        ----------
        worker_tag :
            Tag of the worker to be removed.

        Returns
        -------

        """
        if worker_tag in self.worker_to_mineral_patch_dict:
            # found the worker, get the min tag before deleting
            min_patch_tag: int = self.worker_to_mineral_patch_dict[worker_tag]
            del self.worker_to_mineral_patch_dict[worker_tag]
            if worker_tag in self.worker_tag_to_townhall_tag:
                del self.worker_tag_to_townhall_tag[worker_tag]

            # using the min patch tag, we can remove from other collection
            self.mineral_patch_to_list_of_workers[min_patch_tag].remove(worker_tag)

    def _remove_worker_from_vespene(self, worker_tag: int) -> None:
        """Remove worker from internal data structures.

        This happens if worker gets assigned to do something else, or removing workers
        from gas.

        Parameters
        ----------
        worker_tag :
            Tag of the worker to be removed.

        Returns
        -------

        """
        if worker_tag in self.worker_to_geyser_dict:
            # found the worker, get the gas building tag before deleting
            gas_building_tag: int = self.worker_to_geyser_dict[worker_tag]
            del self.worker_to_geyser_dict[worker_tag]
            if worker_tag in self.worker_tag_to_townhall_tag:
                del self.worker_tag_to_townhall_tag[worker_tag]

            # using the gas building tag, we can remove from other collection
            self.geyser_to_list_of_workers[gas_building_tag].remove(worker_tag)

    def select_worker(
        self,
        target_position: Point2,
        force_close: bool = False,
        select_persistent_builder: bool = False,
        only_select_persistent_builder: bool = False,
        min_health_perc: float = 0.0,
        min_shield_perc: float = 0.0,
    ) -> Optional[Unit]:
        """Select a worker.

        This way we can select one assigned to a far mineral patch.

        Notes
        -----
        Make sure to change the worker role once selected, otherwise it will be selected
        to mine again. This doesn't select workers from geysers, so make sure to remove
        workers from gas if low on workers.


        Parameters
        ----------
        target_position :
            Location to get the closest workers to.
        force_close :
            Select the available worker closest to `target_position` if True.
        select_persistent_builder :
            If True we can select the persistent_builder if it's available.
        only_select_persistent_builder :
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
        target_position = target_position.position
        # maybe we can quickly select the persistent worker
        if select_persistent_builder:
            persistent_workers: Units = self.manager_mediator.get_units_from_role(
                role=UnitRole.PERSISTENT_BUILDER
            )
            # only select worker if it's not in the building tracker
            for worker in persistent_workers:
                if (
                    not worker.is_constructing_scv
                    and worker not in self.manager_mediator.get_building_tracker_dict
                ):
                    return worker

        if only_select_persistent_builder:
            return

        workers: Units = self.manager_mediator.get_units_from_roles(
            roles={UnitRole.GATHERING, UnitRole.IDLE}, unit_type=self.ai.worker_type
        ).filter(lambda u: u.health_percentage >= min_health_perc)
        if self.ai.race == Race.Protoss and min_shield_perc > 0.0:
            workers = workers.filter(lambda u: u.shield_percentage >= min_shield_perc)
        # there is a chance we have no workers
        if not workers or not target_position:
            return

        # if there are workers not assigned to mine (probably long distance mining)
        # choose one of those and return
        unassigned_workers: Units = workers.tags_not_in(
            list(self.worker_to_mineral_patch_dict) + list(self.worker_to_geyser_dict)
        )
        if unassigned_workers and not force_close:
            worker: Unit = cy_closest_to(target_position, unassigned_workers)
            self.remove_worker_from_mineral(worker.tag)
            return worker

        if available_workers := workers.filter(
            lambda w: w.tag in self.worker_to_mineral_patch_dict
            and not w.is_carrying_resource
        ):
            # find townhalls with plenty of mineral patches
            townhalls: list[Unit] = cy_sorted_by_distance_to(
                self.ai.townhalls.filter(
                    lambda th: th.is_ready
                    and self.ai.mineral_field.closer_than(10, th).amount >= 8
                ),
                target_position,
            )
            # seems there are no townhalls with plenty of resources, don't be fussy at
            # this point
            if not townhalls:
                worker = cy_closest_to(target_position, available_workers)
                self.remove_worker_from_mineral(worker.tag)
                return worker

            # go through townhalls, we loop through the min fields by distance to
            # townhall that way there is a good chance we pick a worker at a far mineral
            # patch
            for townhall in townhalls:
                minerals_sorted_by_distance: list[Unit] = cy_sorted_by_distance_to(
                    self.ai.mineral_field.closer_than(10, townhall), townhall.position
                )
                for mineral in reversed(minerals_sorted_by_distance):
                    # we have record of the patch, with some worker tags saved
                    if mineral.tag in self.mineral_patch_to_list_of_workers:
                        if force_close:
                            if close_workers := available_workers.filter(
                                lambda w: w.tag
                                in self.mineral_patch_to_list_of_workers[mineral.tag]
                                and cy_distance_to_squared(
                                    w.position, townhall.position
                                )
                                < 100.0
                            ):
                                worker: Unit = cy_closest_to(
                                    target_position, close_workers
                                )
                                self.remove_worker_from_mineral(worker.tag)
                                return worker
                        else:
                            # try to get a worker at this patch that is not carrying
                            # resources
                            if _workers := available_workers.filter(
                                lambda w: w.tag
                                in self.mineral_patch_to_list_of_workers[mineral.tag]
                                and not w.is_carrying_resource
                                and not w.is_collecting
                            ):
                                worker: Unit = _workers.first
                                # make sure to remove worker, so a new one
                                # can be assigned to mine
                                self.remove_worker_from_mineral(worker.tag)
                                return worker

            # somehow got here without finding a worker, any worker will do
            worker: Unit = cy_closest_to(target_position, available_workers)
            self.remove_worker_from_mineral(worker.tag)
            return worker

    def _assign_workers(self, workers: Units) -> None:
        """Assign workers to mineral patches and gas buildings.

        Parameters
        ----------
        workers :
            Workers to be assigned.

        Returns
        -------

        """
        if not workers or not self.ai.townhalls:
            return

        # This takes priority, ok to remove from minerals
        if self.ai.gas_buildings:
            self._assign_worker_to_gas_buildings(self.ai.gas_buildings)

        if self.available_minerals:
            unassigned_workers: Units = workers.filter(
                lambda u: u.tag not in self.worker_to_geyser_dict
                and u.tag not in self.worker_to_mineral_patch_dict
            )
            self._assign_workers_to_mineral_patches(
                self.available_minerals, unassigned_workers
            )

    def _assign_worker_to_gas_buildings(self, gas_buildings: Units) -> None:
        """Select a worker and assign it to the nearest available gas building.

        We only assign one worker per step, with the hope of grabbing drones on far
        mineral patches.

        Parameters
        ----------
        gas_buildings :
            Completed gas mining structures.

        Returns
        -------

        """
        if not self.ai.townhalls:
            return

        for gas in gas_buildings.ready:
            # don't assign if there is no townhall nearby
            if not self.ai.townhalls.closer_than(12, gas):
                continue
            # too many workers assigned, this can happen if we want to pull workers off
            # gas
            if (
                len(self.geyser_to_list_of_workers.get(gas.tag, []))
                > self.workers_per_gas
            ):
                workers_on_gas: Units = self.ai.workers.tags_in(
                    self.geyser_to_list_of_workers[gas.tag]
                )
                if workers_on_gas:
                    self._remove_worker_from_vespene(workers_on_gas.first.tag)
                continue
            # already perfect amount of workers assigned
            if (
                len(self.geyser_to_list_of_workers.get(gas.tag, []))
                == self.workers_per_gas
            ):
                continue

            # Assign worker closest to the gas building
            worker: Optional[Unit] = self.select_worker(gas.position, force_close=True)

            if not worker or worker.tag in self.geyser_to_list_of_workers:
                continue
            if (
                len(self.geyser_to_list_of_workers.get(gas.tag, []))
                < self.workers_per_gas
            ):
                if len(self.geyser_to_list_of_workers.get(gas.tag, [])) == 0:
                    self.geyser_to_list_of_workers[gas.tag] = {worker.tag}
                else:
                    if worker.tag not in self.geyser_to_list_of_workers[gas.tag]:
                        self.geyser_to_list_of_workers[gas.tag].add(worker.tag)
                self.worker_to_geyser_dict[worker.tag] = gas.tag
                self.worker_tag_to_townhall_tag[worker.tag] = cy_closest_to(
                    gas.position, self.ai.townhalls
                ).tag
                # if this drone was collecting minerals, we need to remove it
                self.remove_worker_from_mineral(worker.tag)
                break

    def _assign_workers_to_mineral_patches(
        self, available_minerals: Units, workers: Units
    ) -> None:
        """Given some minerals and workers, assign two to each mineral patch.

        Thanks to burny's example worker stacking code:
        https://github.com/BurnySc2/python-sc2/blob/develop/examples/worker_stack_bot.py


        Parameters
        ----------
        available_minerals :
            Available mineral patches.
        workers :
            Workers to be assigned.

        Returns
        -------

        """
        if len(workers) == 0 or not self.ai.townhalls:
            return

        _minerals: Units = available_minerals

        if self.initial_worker_split:
            self.initial_worker_split = False
            self._assign_initial_workers(_minerals, workers)
            return

        for worker in workers:
            # run out of minerals to assign
            if not _minerals:
                return
            if (
                worker.tag in self.worker_to_mineral_patch_dict
                or worker.tag in self.worker_to_geyser_dict
            ):
                continue

            if self.ai.time < 120:
                mineral: Unit = cy_closest_to(worker.position, _minerals)
            else:
                # early game threats, stick to main base where possible
                if (
                    self.ai.time < 300.0
                    and self.manager_mediator.get_main_ground_threats_near_townhall
                ):
                    mineral: Unit = cy_closest_to(self.ai.start_location, _minerals)
                else:
                    # find the closest mineral, then find the nearby minerals that are
                    # closest to the townhall
                    closest_mineral: Unit = cy_closest_to(worker.position, _minerals)
                    nearby_minerals: Units = _minerals.closer_than(10, closest_mineral)
                    th: Unit = cy_closest_to(
                        closest_mineral.position, self.ai.townhalls
                    )
                    mineral: Unit = cy_closest_to(th.position, nearby_minerals)

            if len(self.mineral_patch_to_list_of_workers.get(mineral.tag, [])) < 2:
                self._assign_worker_to_patch(mineral, worker)

            # enough have been assigned to this patch, don't consider it on next
            # iteration over loop
            if len(self.mineral_patch_to_list_of_workers.get(mineral.tag, [])) >= 2:
                _minerals.remove(mineral)

    def _assign_worker_to_patch(self, mineral_field: Unit, worker: Unit) -> None:
        """Perform bookkeeping for assigning a worker to a mineral field.

        Parameters
        ----------
        mineral_field :
            Mineral field the worker is being assigned to.
        worker :
            The worker being assigned to the mineral field.

        Returns
        -------

        """
        mineral_tag: int = mineral_field.tag
        worker_tag: int = worker.tag
        if len(self.mineral_patch_to_list_of_workers.get(mineral_tag, [])) == 0:
            self.mineral_patch_to_list_of_workers[mineral_tag] = {worker_tag}
        else:
            if worker_tag not in self.mineral_patch_to_list_of_workers[mineral_tag]:
                self.mineral_patch_to_list_of_workers[mineral_tag].add(worker_tag)
        self.worker_to_mineral_patch_dict[worker_tag] = mineral_tag
        self.worker_tag_to_townhall_tag[worker_tag] = cy_closest_to(
            mineral_field.position, self.ai.townhalls
        ).tag

    def _assign_initial_workers(self, minerals: Units, workers: Units) -> None:
        """Special method for initial workers to split perfectly at the start.

        Close mineral patches will be doubled up and one worker will be assigned to each
        of the four remaining patches.

        Parameters
        ----------
        minerals :
            Mineral fields on the map.
        workers :
            Starting workers.

        Returns
        -------

        """
        sorted_minerals: list[Unit] = cy_sorted_by_distance_to(
            minerals, self.ai.start_location
        )
        assigned_workers: Set[int] = set()
        for i, mineral in enumerate(sorted_minerals):
            leftover_workers: list[Unit] = cy_sorted_by_distance_to(
                workers.tags_not_in(assigned_workers), mineral.position
            )
            # closest 4 patches assign 2 drones, then one on each
            take: int = 2 if i <= 3 else 1
            new_workers: list[Unit] = leftover_workers[:take]
            for w in new_workers:
                self._assign_worker_to_patch(mineral, w)
                assigned_workers.add(w.tag)

    def _remove_workers_from_gas_at_count(self, vespene_count: int = 100) -> None:
        """Precisely control when workers should be pulled off gas.

        This is most useful at the start of the game, and probably would only work with
        one geyser.

        Parameters
        ----------
        vespene_count :
            Target vespene count to end up with when all workers have been pulled off of
            gas.

        Returns
        -------

        """
        if self.ai.vespene <= vespene_count - 12:
            self.workers_per_gas = 3
        elif self.ai.vespene <= vespene_count - 8:
            self.workers_per_gas = 2
        elif self.ai.vespene <= vespene_count - 4:
            self.workers_per_gas = 1
        elif self.ai.vespene >= vespene_count:
            self.workers_per_gas = 0

    def on_unit_destroyed(self, unit_tag: int) -> None:
        """
        If a townhall or worker dies, make sure to clean it up from our data structures
        @param unit_tag:
        @return:
        """
        self.on_townhall_destroyed(unit_tag)
        if unit_tag in self.worker_to_mineral_patch_dict:
            self.remove_worker_from_mineral(unit_tag)
        if unit_tag in self.worker_to_geyser_dict:
            self._remove_worker_from_vespene(unit_tag)

    def on_townhall_destroyed(self, th_tag: int) -> None:
        """Unassign workers when a townhall has been destroyed.

        They'll get reassigned automatically.

        Parameters
        ----------
        th_tag

        Returns
        -------

        """
        for th in self.cached_townhalls:
            if th_tag == th.tag:
                # find a safe path for workers to get out
                self._remove_assigned_workers_from_base(th.position)

    def _remove_assigned_workers_from_base(self, th_position) -> None:
        """If a townhall dies, unassign workers from that base.

        Parameters
        ----------
        th_position :
            Position of the townhall that was destroyed.

        Returns
        -------

        """
        close_min_fields: Units = self.ai.mineral_field.filter(
            lambda mf: mf.distance_to(th_position) < 10
        )
        if close_min_fields:
            for min_field in close_min_fields:
                self._remove_mineral_field(min_field.tag)

        close_gas_buildings: Units = self.ai.gas_buildings.filter(
            lambda gb: gb.distance_to(th_position) < 10
        )
        if close_gas_buildings:
            for gas_building in close_gas_buildings:
                self._remove_gas_building(gas_building.tag)

    def _remove_gas_building(self, gas_building_tag) -> None:
        """Remove gas building and assigned workers from bookkeeping.

        Parameters
        ----------
        gas_building_tag :
            Tag of the gas building to be removed.

        Returns
        -------

        """
        if gas_building_tag in self.geyser_to_list_of_workers:
            del self.geyser_to_list_of_workers[gas_building_tag]
            self.worker_to_geyser_dict = {
                key: val
                for key, val in self.worker_to_geyser_dict.items()
                if val != gas_building_tag
            }

    def _remove_mineral_field(self, mineral_field_tag: int) -> None:
        """Remove mineral field and assigned workers from bookkeeping.

        Parameters
        ----------
        mineral_field_tag :
            Tag of the mineral field to be removed.

        Returns
        -------

        """
        if mineral_field_tag in self.mineral_patch_to_list_of_workers:
            del self.mineral_patch_to_list_of_workers[mineral_field_tag]
            self.worker_to_mineral_patch_dict = {
                key: val
                for key, val in self.worker_to_mineral_patch_dict.items()
                if val != mineral_field_tag
            }

    def _create_resource_to_worker_object_dict(
        self, resource_dict: Dict[int, Unit], resource_type: str
    ) -> Dict[Unit, Units]:
        """Create dictionary where

        The key is a mineral field or gas building and tag the value is a Units of
        workers assigned to gather from that resource.

        Parameters
        ----------
        resource_dict :
            Dictionary of tags to unit objects for the resources.
        resource_type :
            Mineral or gas

        Returns
        -------
        Dict[Unit, Units] :
            Resource Unit to Units of Workers mining it

        """
        resource_to_workers: DefaultDict[Unit, List[Unit]] = defaultdict(list)
        if resource_type == MINERAL:
            worker_to_resource: Dict[int, int] = self.worker_to_mineral_patch_dict
        else:
            worker_to_resource: Dict[int, int] = self.worker_to_geyser_dict
        for worker in self.ai.workers:
            if worker.tag in worker_to_resource:
                resource_tag: int = worker_to_resource[worker.tag]
                resource_object: Optional[Unit] = resource_dict.get(resource_tag, None)
                if resource_object is None:
                    if resource_type == MINERAL:
                        self._remove_mineral_field(resource_tag)
                    else:
                        self._remove_gas_building(resource_tag)
                else:
                    resource_to_workers[resource_object].append(worker)
        return {
            resource: Units(resource_to_workers[resource], self.ai)
            for resource in resource_to_workers
        }

    def _calculate_mineral_targets(self) -> None:
        """Calculate targets for Move commands towards mineral fields when speed mining.

        Thanks to sharpy:
        https://github.com/DrInfy/sharpy-sc2/blob/404d32f55a3f8630fa298d1c6331fcc5b06284
        14/sharpy/plans/tactics/speed_mining.py#L78

        Returns
        -------

        """
        mining_radius: float = self.MINING_RADIUS
        for mf in self.ai.mineral_field:
            target: Point2 = mf.position
            center = target.closest(self.ai.expansion_locations_list)
            target = target.towards(center, mining_radius)
            close = self.ai.mineral_field.closer_than(mining_radius, target)
            for mf2 in close:
                if mf2.tag != mf.tag:
                    points = self._get_intersections(
                        mf.position.x,
                        mf.position.y,
                        mining_radius,
                        mf2.position.x,
                        mf2.position.y,
                        mining_radius,
                    )
                    if len(points) == 2:
                        target = center.closest(points)
            self.mineral_target_dict[mf.position] = target

    @staticmethod
    def _get_intersections(
        x0: float, y0: float, r0: float, x1: float, y1: float, r1: float
    ) -> List[Point2]:
        """Get intersection of two circles.

        Thanks to sharpy:
        https://github.com/DrInfy/sharpy-sc2/blob/993889100dd091e785b193aefe4edc4551f69e
        2c/sharpy/sc2math.py#L39

        Parameters
        ----------
        x0 :
            x-coordinate of the center circle 1
        y0 :
            y-coordinate of the center circle 1
        r0 :
            radius of circle 1
        x1 :
            x-coordinate of the center circle 2
        y1 :
            y-coordinate of the center circle 2
        r1 :
            radius of circle 2

        Returns
        -------
        List[Point2] :
            The intersection points of the circles.

        """
        # circle 1: (x0, y0), radius r0
        # circle 2: (x1, y1), radius r1

        d = math.sqrt((x1 - x0) ** 2 + (y1 - y0) ** 2)

        # non-intersecting
        if d > r0 + r1:
            return []
        # One circle within other
        if d < abs(r0 - r1):
            return []
        # coincident circles
        if d == 0 and r0 == r1:
            return []
        else:
            a = (r0**2 - r1**2 + d**2) / (2 * d)
            h = math.sqrt(r0**2 - a**2)
            x2 = x0 + a * (x1 - x0) / d
            y2 = y0 + a * (y1 - y0) / d
            x3 = x2 + h * (y1 - y0) / d
            y3 = y2 - h * (x1 - x0) / d

            x4 = x2 - h * (y1 - y0) / d
            y4 = y2 + h * (x1 - x0) / d

            return [Point2((x3, y3)), Point2((x4, y4))]

    def _print_debug_information(self) -> None:
        """Print debug info on speed mining to the screen.

        Users on Discord were testing on Romanticide with only 12 workers and recording
        results at frame 6720.
        Best: 3975 (how?)
        3875 - 3895 seems typical for most bots

        Returns
        -------

        """
        if self.ai.state.game_loop == 6720:
            print(
                f"{self.ai.time_formatted} Mined a total of {int(self.ai.minerals)}\
                 minerals"
            )

            print(
                f"{self.ai.time_formatted} Mined a total of\
                 {int(self.ai.state.score.collected_vespene)} vespene"
            )
