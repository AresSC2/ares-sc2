from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, Union

from cython_extensions import cy_closest_to, cy_distance_to_squared, cy_towards
from loguru import logger
from sc2.ids.ability_id import AbilityId
from sc2.position import Point2
from sc2.unit import Unit

from ares.behaviors.combat.individual.combat_individual_behavior import (
    CombatIndividualBehavior,
)
from ares.managers.manager_mediator import ManagerMediator

if TYPE_CHECKING:
    from ares import AresBot

TOWNHALL_RADIUS: float = 2.75


@dataclass
class SpeedMining(CombatIndividualBehavior):
    """Speed mine worker at provided townhall and target resource.

    Example:
    ```py
    from ares.behaviors.combat.individual import SpeedMining

    self.register_behavior(
        SpeedMining(
            worker, self.mineral_field[0], worker.position, resource_position
        )
    )
    ```

    Attributes:
        worker: The worker to mine with.
        target: The resource to mine.
        worker_position: Position of worker.
        resource_target_pos: Position in front or resource to
            move to before queueing a mine command.
        distance_to_townhall_factor: How far away from th to
            move command. Default is 1.08
        townhall: Townhall worker is assigned to.
            Default to None (will calculate closest if so)

    """

    worker: Unit
    target: Union[Point2, Unit]
    worker_position: Point2
    resource_target_pos: Point2
    distance_to_townhall_factor: float = 1.08
    townhall: Optional[Unit] = None

    def execute(self, ai: "AresBot", config: dict, mediator: ManagerMediator) -> bool:
        if not ai.townhalls:
            logger.warning(
                f"{ai.time_formatted} Attempting to speed mine with no townhalls"
            )
            return False

        if not ai.mineral_field:
            logger.warning(
                f"{ai.time_formatted} Attempting to speed mine with no mineral fields"
            )
            return False

        worker: Unit = self.worker
        len_orders: int = len(worker.orders)

        # do some further processing here or the orders
        # but in general if worker has 2 orders it is speedmining
        if len_orders == 2:
            return True

        if (worker.is_returning or worker.is_carrying_resource) and len_orders < 2:
            if not self.townhall:
                self.townhall = cy_closest_to(self.worker_position, ai.townhalls)

            target_pos: Point2 = self.townhall.position

            target_pos: Point2 = Point2(
                cy_towards(
                    target_pos,
                    self.worker_position,
                    TOWNHALL_RADIUS * self.distance_to_townhall_factor,
                )
            )

            if 0.5625 < cy_distance_to_squared(self.worker_position, target_pos) < 4.0:
                worker.move(target_pos)
                worker(AbilityId.SMART, self.townhall, True)
                return True
            # not at right distance to get boost command, but doesn't have return
            # resource command for some reason
            elif not worker.is_returning:
                worker(AbilityId.SMART, self.townhall)
                return True

        elif not worker.is_returning and len_orders < 2:
            min_distance: float = 0.5625 if self.target.is_mineral_field else 0.01
            max_distance: float = 4.0 if self.target.is_mineral_field else 0.25
            if (
                min_distance
                < cy_distance_to_squared(self.worker_position, self.resource_target_pos)
                < max_distance
                or worker.is_idle
            ):
                worker.move(self.resource_target_pos)
                worker(AbilityId.SMART, self.target, True)
                return True

        # on rare occasion above conditions don't hit and worker goes idle
        elif worker.is_idle or not worker.is_moving:
            if worker.is_carrying_resource:
                worker.return_resource(self.townhall)
            else:
                worker.gather(self.target)
            return True

        return False
