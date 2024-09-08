from dataclasses import dataclass
from typing import TYPE_CHECKING

from sc2.ids.unit_typeid import UnitTypeId as UnitID

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

    Attributes
    ----------
    to_count : int
        The target count of workers we want to hit.
    """

    to_count: int

    def execute(self, ai: "AresBot", config: dict, mediator: ManagerMediator) -> bool:
        worker_type: UnitID = ai.worker_type
        if (
            ai.can_afford(worker_type)
            and ai.townhalls.idle
            and ai.supply_workers < self.to_count
        ):
            return SpawnController(
                {
                    worker_type: {"proportion": 1.0, "priority": 0},
                }
            ).execute(ai, config, mediator)

        return False
