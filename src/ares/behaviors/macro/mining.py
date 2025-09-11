from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable, Optional

import numpy as np
from cython_extensions.units_utils import cy_sorted_by_distance_to
from loguru import logger
from sc2.data import Race
from sc2.ids.ability_id import AbilityId
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units

from ares.behaviors.macro.speed_mining import SpeedMining

if TYPE_CHECKING:
    from ares import AresBot

from cython_extensions import (
    cy_attack_ready,
    cy_closest_to,
    cy_distance_to,
    cy_distance_to_squared,
    cy_in_attack_range,
    cy_pick_enemy_target,
    cy_towards,
)

from ares.behaviors.macro import MacroBehavior
from ares.consts import GAS_BUILDINGS, MINING, TOWNHALL_DISTANCE_FACTOR, UnitRole
from ares.managers.manager_mediator import ManagerMediator

TOWNHALL_RADIUS: float = 2.75
# how far from townhall should we return speed miners to
TOWNHALL_TARGET: float = TOWNHALL_RADIUS * 1.21


@dataclass
class Mining(MacroBehavior):
    """Handle worker mining control.

    Note: Could technically be `CombatBehavior`, but is treated here as a
    MacroBehavior since many tasks are carried out.

    Example:
    ```py
    from ares.behaviors.macro import Mining

    self.register_behavior(Mining())
    ```

    Attributes:
        flee_at_health_perc: If worker is in danger, at what
            health percentage should it flee? Defaults to 0.5.
        keep_safe: Should workers flee if they are in danger?
            Defaults to True.
        long_distance_mine: Can the worker long distance mine if it has nothing to do?
            Defaults to True.
        mineral_boost: Turn mineral boosting on or off. Defaults to True.
        vespene_boost: Turn vespene boosting on or off
            (only active when workers_per_gas < 3).
            WARNING: VESPENE BOOSTING CURRENTLY NOT WORKING.
            Defaults to True.
        workers_per_gas: Control how many workers are assigned to each gas.
            Defaults to 3.
        self_defence_active: If set to True, workers will have some basic defence.
            Certain workers will attack enemy in range. Defaults to True.
        safe_long_distance_mineral_fields: Used internally, set when a worker starts
            long distance mining. Defaults to None.
        weight_safety_limit: Workers will flee if enemy influence is above this number.
            Defaults to 12.0

    """

    flee_at_health_perc: float = 0.5
    keep_safe: bool = True
    long_distance_mine: bool = True
    mineral_boost: bool = True
    vespene_boost: bool = False
    workers_per_gas: int = 3
    self_defence_active: bool = True
    safe_long_distance_mineral_fields: Optional[Units] = None
    locked_action_tags: dict[int, float] = field(default_factory=dict)
    weight_safety_limit: float = 12.0

    def execute(self, ai: "AresBot", config: dict, mediator: ManagerMediator) -> bool:
        workers: Units = mediator.get_units_from_role(
            role=UnitRole.GATHERING,
            unit_type=ai.worker_type,
        )
        if not workers:
            return False

        resources_dict: dict[int, Unit] = ai.unit_tag_dict
        health_perc: float = self.flee_at_health_perc
        avoidance_grid: np.ndarray = mediator.get_ground_avoidance_grid
        grid: np.ndarray = mediator.get_ground_grid
        mineral_patch_to_list_of_workers: dict[
            int, set[int]
        ] = mediator.get_mineral_patch_to_list_of_workers
        path_find: Callable = mediator.find_path_next_point
        pos_safe: Callable = mediator.is_position_safe
        th_dist_factor: float = config[MINING][TOWNHALL_DISTANCE_FACTOR]
        worker_to_geyser_dict: dict[int, int] = mediator.get_worker_to_vespene_dict
        worker_to_mineral_patch_dict: dict[
            int, int
        ] = mediator.get_worker_to_mineral_patch_dict
        worker_to_th: dict[int, int] = mediator.get_worker_tag_to_townhall_tag
        # for each mineral tag, get the position in front of the mineral
        min_target: dict[int, Point2] = mediator.get_mineral_target_dict
        main_enemy_ground_threats: Optional[Units] = None
        race: Race = ai.race
        if self.self_defence_active:
            main_enemy_ground_threats = mediator.get_main_ground_threats_near_townhall

        for worker in workers:
            worker_position: Point2 = worker.position
            worker_tag: int = worker.tag
            resource: Optional[Unit] = None
            resource_position: Optional[Point2] = None
            resource_tag: int = -1

            assigned_mineral_patch: bool = worker_tag in worker_to_mineral_patch_dict
            assigned_gas_building: bool = worker_tag in worker_to_geyser_dict
            dist_to_resource: float = 15.0
            if assigned_mineral_patch or assigned_gas_building:
                resource_tag: int = (
                    worker_to_mineral_patch_dict[worker_tag]
                    if assigned_mineral_patch
                    else worker_to_geyser_dict[worker_tag]
                )
                # using try except is faster than dict.get()
                try:
                    _resource = resources_dict[resource_tag]
                    resource_position = _resource.position
                    resource_tag = _resource.tag
                    resource = _resource
                    dist_to_resource = cy_distance_to(
                        worker_position, resource_position
                    )
                    if (
                        resource.type_id in GAS_BUILDINGS
                        and resource.vespene_contents == 0
                    ):
                        mediator.remove_gas_building(gas_building_tag=resource_tag)

                except KeyError:
                    # Mined out or no vision? Remove it
                    if assigned_mineral_patch:
                        mediator.remove_mineral_field(mineral_field_tag=resource_tag)
                    else:
                        mediator.remove_gas_building(gas_building_tag=resource_tag)
                    continue

            perc_health: float = (
                worker.health_percentage
                if race != Race.Protoss
                else worker.shield_health_percentage
            )
            worker_safe: bool = pos_safe(grid=grid, position=worker_position)
            # keeping worker safe is first priority
            if self.keep_safe and (
                # lib zone / nukes etc
                not pos_safe(grid=avoidance_grid, position=worker_position)
                # retreat based on self.flee_at_health_perc value
                or (perc_health <= health_perc and not worker_safe)
                or not pos_safe(
                    grid=grid,
                    position=worker_position,
                    weight_safety_limit=self.weight_safety_limit,
                )
            ):
                self._keep_worker_safe(mediator, grid, worker)

            elif (
                not worker_safe
                and main_enemy_ground_threats
                and self._worker_attacking_enemy(ai, dist_to_resource, worker)
            ):
                pass

            # do we have record of this worker? If so mine from the relevant resource
            elif ai.townhalls and (assigned_mineral_patch or assigned_gas_building):
                # we are far away, path to min field to avoid enemies
                if dist_to_resource > 6.0 and not worker.is_carrying_resource:
                    worker.move(
                        path_find(
                            start=worker_position,
                            target=resource_position,
                            grid=grid,
                        )
                    )

                # fix realtime bug where worker is stuck with a move command
                # but already returned minerals
                elif (
                    len(worker.orders) == 1
                    and worker.orders[0].ability.id == AbilityId.MOVE
                    and ai.ready_townhalls
                    and worker.order_target
                    == cy_closest_to(worker_position, ai.ready_townhalls).tag
                    # shift worker to correct resource if it ends up on wrong one
                ) or (worker.is_gathering and worker.order_target != resource_tag):
                    # target being the mineral
                    worker(AbilityId.SMART, resource)

                elif (self.mineral_boost and assigned_mineral_patch) or (
                    self.vespene_boost and self.workers_per_gas < 3
                ):
                    self._do_mining_boost(
                        ai,
                        th_dist_factor,
                        min_target,
                        resource,
                        worker,
                        worker_to_th,
                        worker_position,
                        resource_position,
                    )
                else:
                    self._do_standard_mining(ai, worker, resource)

            # nowhere for this worker to go, long distance mining
            elif self.long_distance_mine and ai.minerals and ai.townhalls:
                self._long_distance_mining(
                    ai,
                    mediator,
                    grid,
                    worker,
                    mineral_patch_to_list_of_workers,
                    worker_position,
                )

            # this worker really has nothing to do, keep it safe at least
            # don't mine from anywhere since user requested no `long_distance_mine`
            elif not pos_safe(grid=grid, position=worker_position):
                self._keep_worker_safe(mediator, grid, worker)

        mediator.set_workers_per_gas(amount=self.workers_per_gas)
        return True

    @staticmethod
    def _keep_worker_safe(
        mediator: ManagerMediator, grid: np.ndarray, worker: Unit
    ) -> None:
        """Logic for keeping workers in danger safe.

        Parameters:
            mediator: ManagerMediator used for getting information from
                other managers.
            grid: Ground grid with enemy influence.
            worker: Worker to keep safe.
        """
        worker.move(
            mediator.find_closest_safe_spot(from_pos=worker.position, grid=grid)
        )

    def _do_standard_mining(self, ai: "AresBot", worker: Unit, resource: Unit) -> None:
        worker_tag: int = worker.tag
        # prevent spam clicking workers on patch to reduce APM
        if worker_tag in self.locked_action_tags:
            if ai.time > self.locked_action_tags[worker_tag] + 0.5:
                self.locked_action_tags.pop(worker_tag)
            return
        # moved worker from gas
        if worker.is_carrying_vespene and resource.is_mineral_field:
            worker.return_resource()
            self.locked_action_tags[worker_tag] = ai.time
        else:
            # leave worker alone
            if len(worker.orders) > 0:
                current_order = worker.orders[0]
                if current_order.ability.id == AbilityId.HARVEST_RETURN:
                    return

            # work out when we need to issue command to mine resource
            if worker.is_idle or (
                cy_distance_to_squared(worker.position, resource.position) > 81.0
                and worker.order_target
                and worker.order_target != resource
            ):
                worker.gather(resource)
                self.locked_action_tags[worker_tag] = ai.time
                return

            # force worker to stay on correct resource
            # in game auto mining will sometimes shift worker
            if (
                not worker.is_carrying_minerals
                and not worker.is_carrying_vespene
                and worker.order_target != resource.tag
            ):
                worker.gather(resource)
                # to reduce apm we prevent spam clicking on same mineral
                self.locked_action_tags[worker_tag] = ai.time

    def _long_distance_mining(
        self,
        ai: "AresBot",
        mediator: ManagerMediator,
        grid: np.ndarray,
        worker: Unit,
        mineral_patch_to_list_of_workers: dict[int, set[int]],
        worker_position: Point2,
    ) -> None:
        """Logic for long distance mining.

        Parameters
        ----------
        ai : AresBot
            Bot object that will be running the game.
        mediator : ManagerMediator
            Used for getting information from other managers.
        grid : np.ndarray
            Ground grid with enemy influence.
        worker: Unit
            Worker we want to issue actions to.
        mineral_patch_to_list_of_workers: dict
            Record of assigned mineral patches, so we know which ones to avoid.
        worker_position :
            Pass this in for optimization purposes.
        Returns
        -------

        """
        if (
            worker.is_gathering
            and worker.order_target not in mediator.get_mineral_patch_to_list_of_workers
        ):
            return

        completed_bases: Units = ai.townhalls.ready
        # there is nowhere to return resources!
        if not completed_bases:
            return

        if not self.safe_long_distance_mineral_fields:
            self.safe_long_distance_mineral_fields = (
                self._safe_long_distance_mineral_fields(ai, mediator)
            )

        target_mineral: Optional[Unit] = None

        # on route to a far mineral patch
        if (
            (not worker.is_gathering and not worker.is_carrying_resource)
            # mining somewhere we manage ourselves
            or (
                worker.order_target
                and worker.order_target in mineral_patch_to_list_of_workers
            )
        ):
            # if there is a pending base, we should mine from there
            pending_bases: Units = ai.townhalls.filter(lambda th: not th.is_ready)
            if pending_bases and ai.mineral_field:
                target_base: Unit = cy_closest_to(worker_position, pending_bases)
                target_mineral = cy_closest_to(target_base.position, ai.mineral_field)
            # no pending base, find a mineral field
            elif self.safe_long_distance_mineral_fields:
                # early game, get closest to natural
                if ai.time < 260.0:
                    target_mineral = cy_closest_to(
                        mediator.get_own_nat, self.safe_long_distance_mineral_fields
                    )
                else:
                    target_mineral = cy_closest_to(
                        worker.position, self.safe_long_distance_mineral_fields
                    )

            if target_mineral:
                target_mineral_position: Point2 = target_mineral.position
                if (
                    not mediator.is_position_safe(
                        grid=grid,
                        position=worker_position,
                    )
                    and cy_distance_to_squared(worker_position, target_mineral_position)
                    > 25.0
                ):
                    move_to: Point2 = mediator.find_path_next_point(
                        start=worker_position,
                        target=target_mineral_position,
                        grid=grid,
                        sense_danger=False,
                    )
                    worker.move(move_to)
                elif ai.mineral_field:
                    if worker.order_target and worker.order_target == target_mineral:
                        return
                    worker.gather(target_mineral)
        # worker is travelling back to a ready townhall
        else:
            if worker.is_returning:
                return
            return_base: Unit = cy_closest_to(worker_position, completed_bases)
            return_base_position: Point2 = return_base.position
            if (
                not mediator.is_position_safe(grid=grid, position=worker_position)
                and cy_distance_to_squared(worker_position, return_base_position) > 64.0
            ):
                move_to: Point2 = mediator.find_path_next_point(
                    start=worker_position,
                    target=return_base_position,
                    grid=grid,
                    sense_danger=False,
                )
                worker.move(move_to)
            else:
                worker.return_resource()

    @staticmethod
    def _do_mining_boost(
        ai,
        distance_to_townhall_factor,
        mineral_target_dict,
        target,
        worker,
        worker_tag_to_townhall_tag,
        worker_position: Point2,
        target_position: Point2,
    ) -> bool:
        """Perform the trick so that worker does not decelerate.

        This avoids worker deceleration when mining by issuing a Move command near a
        mineral patch/townhall and then issuing a Gather or Return command once the
        worker is close enough to immediately perform the action instead of issuing a
        Gather command and letting the SC2 engine manage the worker.

        Parameters:
            ai: Main AresBot object
            distance_to_townhall_factor: Multiplier used for finding the target
                of the Move command when returning resources.
            target: Mineral field or Townhall that the worker should be
                moving toward/performing an action on.
            worker: The worker being boosted.
            worker_tag_to_townhall_tag: The townhall this worker belongs to,
                or where resources will be returned.
            worker_position: Pass in for optimization purposes.
            target_position: Pass in for optimization purposes.

        Returns:
            Whether this method carries out an action
        """

        if target.is_mineral_field or target.is_vespene_geyser:
            try:
                resource_target_pos: Point2 = mineral_target_dict[target_position]
            except KeyError:
                logger.warning(
                    f"{target_position} not found in resource_target_pos, "
                    f"no action will be provided for f{worker.tag}"
                )
                return False
        else:
            resource_target_pos: Point2 = Point2(
                cy_towards(target_position, worker_position, TOWNHALL_TARGET)
            )

        if not target:
            ai.mediator.remove_mineral_field(mineral_field_tag=target.tag)
            ai.mediator.remove_worker_from_mineral(worker_tag=worker.tag)
        elif not target.is_mineral_field and not target.vespene_contents:
            ai.mediator.remove_gas_building(gas_building_tag=target.tag)

        try:
            townhall: Unit = ai.unit_tag_dict[worker_tag_to_townhall_tag[worker.tag]]
        except KeyError:
            townhall: Unit = cy_closest_to(worker_position, ai.townhalls)

        return SpeedMining(
            worker,
            target,
            worker_position,
            resource_target_pos,
            distance_to_townhall_factor,
            townhall,
        ).execute(ai, ai.mediator, ai.config)

    @staticmethod
    def _safe_long_distance_mineral_fields(
        ai: "AresBot", mediator: ManagerMediator
    ) -> list[Unit]:
        """Find mineral fields for long distance miners.

        Parameters:
            ai: Main AresBot object
            mediator: Manager mediator to interact with the managers

        Returns:
            Units object of safe mineral patches if mineral patches still exist
        """
        if not ai.mineral_field:
            return

        assigned_patches: dict[int, set] = mediator.get_mineral_patch_to_list_of_workers
        grid: np.ndarray = mediator.get_ground_grid
        mfs: list[Unit] = cy_sorted_by_distance_to(ai.mineral_field, ai.start_location)
        weight_safety_limit: float = 6.0
        if ai.state.score.collection_rate_minerals < 300:
            weight_safety_limit = 100.0
        safe_mfs: list[Unit] = []
        for mf in mfs:
            if mf in assigned_patches or not mediator.is_position_safe(
                grid=grid, position=mf.position, weight_safety_limit=weight_safety_limit
            ):
                continue
            safe_mfs.append(mf)

        return safe_mfs

    @staticmethod
    def _worker_attacking_enemy(
        ai: "AresBot", dist_to_resource: float, worker: Unit
    ) -> bool:
        if not worker.is_collecting or dist_to_resource > 1.0:
            if enemies := cy_in_attack_range(worker, ai.enemy_units):
                target: Unit = cy_pick_enemy_target(enemies)

                if cy_attack_ready(ai, worker, target):
                    worker.attack(target)
                    return True
        return False
