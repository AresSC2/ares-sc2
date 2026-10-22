from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from sc2.data import Race
from sc2.ids.unit_typeid import UnitTypeId

from ares.behaviors.macro.spawn_controller import SpawnController

if TYPE_CHECKING:
    from ares import AresBot

from ares.behaviors.macro.macro_behavior import MacroBehavior
from ares.managers.manager_mediator import ManagerMediator


@dataclass
class BuildWorkers(MacroBehavior):
    """Finds idle townhalls / larvae and build workers.

    Example:
    ```py
    from ares.behaviors.macro import BuildWorkers

    self.register_behavior(
        BuildWorkers(to_count=80)
    )
    ```

    Attributes:
        to_count: The target count of workers we want to hit.

    """

    to_count: int

    def execute(self, ai: AresBot, config: dict, mediator: ManagerMediator) -> bool:
        worker_type: UnitTypeId = ai.worker_type
        num_to_build: int = self.to_count - int(ai.supply_workers)
        # zerg workers come from larva, so idle townhalls are irrelevant
        can_build_from: bool = bool(
            ai.larva if ai.race == Race.Zerg else ai.townhalls.idle
        )
        if ai.can_afford(worker_type) and can_build_from and num_to_build > 0:
            return SpawnController(
                {
                    worker_type: {"proportion": 1.0, "priority": 0},
                },
                # don't overshoot `to_count`, ie: zerg with lots of larva
                maximum=num_to_build,
            ).execute(ai, config, mediator)

        return False
