from dataclasses import dataclass
from typing import Callable, Optional

import numpy as np
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId as UnitID
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units

from ares import AresBot
from ares.behaviors.macro import MacroBehavior
from ares.consts import MINING, TOWNHALL_DISTANCE_FACTOR, UnitRole, UnitTreeQueryType
from ares.cython_extensions.combat_utils import cy_attack_ready, cy_pick_enemy_target
from ares.cython_extensions.geometry import cy_distance_to
from ares.cython_extensions.units_utils import cy_closest_to, cy_in_attack_range
from ares.managers.manager_mediator import ManagerMediator

TOWNHALL_RADIUS: float = 2.5
WORKER_TYPES: set[UnitID] = {UnitID.DRONE, UnitID.PROBE, UnitID.SCV, UnitID.MULE}


@dataclass
class Mining(MacroBehavior):
    """Handle worker mining control.

    Note: Could technically be `CombatBehavior`, but is treated here as a
    MacroBehavior since many tasks are carried out.

    Attributes
    ----------
    flee_at_health_perc : float, optional
        If worker is in danger, at what health perc should it flee (default is 0.5).
    keep_safe : bool, optional
        Workers flee if they are in danger? (default is True).
    long_distance_mine : bool, optional
        If worker has nothing to do, can it long distance mine (default is True).
    mineral_boost : bool, optional
        Turn mineral boosting off / on (default is True).
    vespene_boost : bool, optional
        Turn vespene boosting off / on (only active when workers_per_gas < 3)
        (default is True).
    workers_per_gas : bool, optional (default: 3)
        Control how many workers are assigned to each gas.
    self_defence_active : bool, optional (default: True)
        If set to True, workers will have some basic defence.
        Certain workers will attack enemy in range.
    safe_long_distance_mineral_fields : Optional[Units], optional (default is None)
        Used internally, value is set if a worker starts long distance mining.
    """

    flee_at_health_perc: float = 0.5
    keep_safe: bool = True
    long_distance_mine: bool = True
    mineral_boost: bool = True
    vespene_boost: bool = True
    workers_per_gas: int = 3
    self_defence_active: bool = True
    safe_long_distance_mineral_fields: Optional[Units] = None

    def execute(self, ai: AresBot, config: dict, mediator: ManagerMediator) -> bool:
        """Execute the mining task (Called from `behavior_executioner.py`).

        Depending on the attributes passed, carry out mining tasks based
        on the bookkeeping found inside `resource_manager`. No need to
        manually call this.

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
        bool :
            bool indicating if this task was executed (always `True` here).
        """
        workers: Units = mediator.get_units_from_role(
            role=UnitRole.GATHERING,
            unit_type=ai.worker_type,
        )
        if not workers:
            return False

        mediator.set_workers_per_gas(amount=self.workers_per_gas)

        resources_dict: dict[int, Unit] = dict(
            (resource.tag, resource) for resource in ai.gas_buildings + ai.mineral_field
        )
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
        if self.self_defence_active:
            main_enemy_ground_threats = mediator.get_main_ground_threats_near_townhall

        for worker in workers:
            worker_position: Point2 = worker.position
            worker_tag: int = worker.tag
            resource: Optional[Unit] = None
            resource_position: Optional[Point2] = None
            resource_tag: int = -1

            # keeping worker safe is first priority
            if self.keep_safe and (
                # lib zone / nukes etc
                not pos_safe(grid=avoidance_grid, position=worker_position)
                # retreat based on self.flee_at_health_perc value
                or (
                    worker.health_percentage <= health_perc
                    and not pos_safe(grid=grid, position=worker_position)
                )
            ):
                self._keep_worker_safe(mediator, grid, worker, worker_position)
                continue

            assigned_mineral_patch: bool = worker_tag in worker_to_mineral_patch_dict
            assigned_gas_building: bool = worker_tag in worker_to_geyser_dict
            dist_to_resource: float = 15.0
            if assigned_mineral_patch or assigned_gas_building:
                resource_tag: int = (
                    worker_to_mineral_patch_dict[worker_tag]
                    if assigned_mineral_patch
                    else worker_to_geyser_dict[worker.tag]
                )
                if _resource := resources_dict.get(resource_tag, None):
                    resource_position = _resource.position
                    resource_tag = _resource.tag
                    resource = _resource
                    dist_to_resource = cy_distance_to(
                        worker_position, resource_position
                    )
                else:
                    # Mined out or no vision? Remove it
                    if assigned_mineral_patch:
                        mediator.remove_mineral_field(mineral_field_tag=resource_tag)
                    else:
                        mediator.remove_gas_building(gas_building_tag=resource_tag)
                    continue

            if main_enemy_ground_threats and self._worker_attacking_enemy(
                ai, dist_to_resource, worker
            ):
                continue

            # do we have record of this worker? If so mine from the relevant resource
            if assigned_mineral_patch or assigned_gas_building:
                # we are far away, path to min field to avoid enemies
                if dist_to_resource > 6.0 and not worker.is_carrying_resource:
                    worker.move(
                        path_find(
                            start=worker_position,
                            target=resource_position,
                            grid=grid,
                        )
                    )

                # shift worker to correct resource if it ends up on wrong one
                elif worker.is_gathering and worker.order_target != resource_tag:
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
                    townhall: Unit = ai.townhalls.closest_to(resource)
                    if assigned_gas_building and (
                        (
                            worker.order_target != resource_tag
                            and worker.order_target != townhall.tag
                        )
                        or not worker.is_collecting
                    ):
                        worker.gather(resource)

            # nowhere for this worker to go, long distance mining
            elif self.long_distance_mine and ai.minerals:
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
                self._keep_worker_safe(mediator, grid, worker, worker_position)

        return True

    @staticmethod
    def _keep_worker_safe(
        mediator: ManagerMediator,
        grid: np.ndarray,
        worker: Unit,
        worker_position: Point2,
    ) -> None:
        """Logic for keeping workers in danger safe.

        Parameters
        ----------
        mediator : ManagerMediator
            ManagerMediator used for getting information from other managers.
        grid : np.ndarray
            Ground grid with enemy influence.
        worker :
            Worker to keep safe.
        worker_position :
            Pass this in for optimization purposes,
            as may have already retrieved it.

        Returns
        -------

        """
        worker.move(
            mediator.find_closest_safe_spot(from_pos=worker_position, grid=grid)
        )

    def _long_distance_mining(
        self,
        ai: AresBot,
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
                target_mineral = self.safe_long_distance_mineral_fields.closest_to(
                    worker
                )

            if target_mineral:
                target_mineral_position: Point2 = target_mineral.position
                if (
                    not mediator.is_position_safe(
                        grid=grid,
                        position=worker_position,
                    )
                    and cy_distance_to(worker_position, target_mineral_position) > 5
                ):
                    move_to: Point2 = mediator.find_path_next_point(
                        start=worker_position,
                        target=target_mineral_position,
                        grid=grid,
                        sense_danger=False,
                    )
                    worker.move(move_to)
                elif ai.mineral_field:
                    worker.gather(target_mineral)
        # worker is travelling back to a ready townhall
        else:
            return_base: Unit = cy_closest_to(worker_position, completed_bases)
            return_base_position: Point2 = return_base.position
            if (
                not mediator.is_position_safe(grid=grid, position=worker_position)
                and cy_distance_to(worker_position, return_base_position) > 8
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
    ) -> None:
        """Perform the trick so that worker does not decelerate.

        This avoids worker deceleration when mining by issuing a Move command near a
        mineral patch/townhall and then issuing a Gather or Return command once the
        worker is close enough to immediately perform the action instead of issuing a
        Gather command and letting the SC2 engine manage the worker.

        Parameters
        ----------
        ai :
            Main AresBot object
        distance_to_townhall_factor :
            Multiplier used for finding the target of the Move command when returning
            resources.
        target :
            Mineral field or Townhall that the worker should be moving toward/performing
            an action on.
        worker :
            The worker being boosted.
        worker_tag_to_townhall_tag :
            The townhall this worker belongs to, or where resources will be returned.
        worker_position :
            Pass in for optimization purposes.
        target_position :
            Pass in for optimization purposes.
        Returns
        -------

        """

        if target.is_mineral_field:
            resource_target_pos: Point2 = mineral_target_dict.get(target_position)
        else:
            resource_target_pos: Point2 = target_position.towards(
                worker, TOWNHALL_RADIUS * 1.21
            )

        closest_th: Unit = cy_closest_to(worker_position, ai.townhalls)

        # fix realtime bug where worker is stuck with a move command but already
        # returned minerals
        if (
            len(worker.orders) == 1
            and worker.orders[0].ability.id == AbilityId.MOVE
            and worker.order_target == closest_th.tag
        ):
            worker(AbilityId.SMART, target)

        elif (worker.is_returning or worker.is_carrying_resource) and len(
            worker.orders
        ) < 2:
            townhall: Optional[Unit] = None
            if worker.tag in worker_tag_to_townhall_tag:
                townhall: Unit = ai.structures.by_tag(
                    worker_tag_to_townhall_tag[worker.tag]
                )
            if not townhall:
                townhall: Unit = closest_th

            target_pos: Point2 = townhall.position
            target_pos = target_pos.towards(
                worker, TOWNHALL_RADIUS * distance_to_townhall_factor
            )

            if 0.75 < cy_distance_to(worker_position, target_pos) < 2:
                worker.move(target_pos)
                worker(AbilityId.SMART, townhall, True)
            # not at right distance to get boost command, but doesn't have return
            # resource command for some reason
            elif not worker.is_returning:
                worker(AbilityId.SMART, townhall)

        elif not worker.is_returning and len(worker.orders) < 2:
            min_distance: float = 0.75 if target.is_mineral_field else 0.1
            max_distance: float = 2.0 if target.is_mineral_field else 0.5
            if (
                min_distance
                < cy_distance_to(worker_position, resource_target_pos)
                < max_distance
                or worker.is_idle
            ):
                worker.move(resource_target_pos)
                worker(AbilityId.SMART, target, True)

        # on rare occasion above conditions don't hit and worker goes idle
        elif worker.is_idle or not worker.is_moving:
            if worker.is_carrying_resource:
                worker.return_resource(closest_th)
            else:
                worker.gather(target)

    @staticmethod
    def _safe_long_distance_mineral_fields(
        ai: AresBot, mediator: ManagerMediator
    ) -> Optional[Units]:
        """Find mineral fields for long distance miners.

        Parameters
        ----------
        ai :
            Main AresBot object
        mediator :
            Manager mediator to interact with the managers

        Returns
        -------
            Optional[Units] :
                Units object of safe mineral patches if mineral patches still exist,
                None otherwise.
        """
        if not ai.mineral_field:
            return

        th_tags: set[int] = ai.townhalls.tags
        mf_to_enemy: dict[int, Units] = mediator.get_units_in_range(
            start_points=ai.mineral_field,
            distances=30,
            query_tree=UnitTreeQueryType.AllEnemy,
            return_as_dict=True,
        )

        mf_to_own: dict[int, Units] = mediator.get_units_in_range(
            start_points=ai.mineral_field,
            distances=8,
            query_tree=UnitTreeQueryType.AllOwn,
            return_as_dict=True,
        )

        enemy_ground_dangerous_tags: set[int] = ai.enemy_units.filter(
            lambda e: e.can_attack_ground and e.type_id not in WORKER_TYPES
        ).tags

        safe_fields = []
        for mf in ai.mineral_field:
            if th_tags & mf_to_own[mf.tag].tags:  # intersection
                # there's a shared tag in our units close to the mineral field and our
                # townhalls
                continue
            else:
                found = False
                for tag in mf_to_enemy[mf.tag].tags:
                    if tag in enemy_ground_dangerous_tags:
                        # there's an enemy nearby
                        found = True
                        break
                if found:
                    continue
                safe_fields.append(mf)
        return Units(safe_fields, ai)

    @staticmethod
    def _worker_attacking_enemy(
        ai: AresBot, dist_to_resource: float, worker: Unit
    ) -> bool:
        if not worker.is_collecting or dist_to_resource > 1.0:
            if enemies := cy_in_attack_range(worker, ai.enemy_units):
                target: Unit = cy_pick_enemy_target(enemies)

                if cy_attack_ready(ai, worker, target):
                    worker.attack(target)
                    return True
        return False
