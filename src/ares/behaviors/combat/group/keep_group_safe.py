from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

import numpy as np
from sc2.unit import Unit
from sc2.units import Units

from ares.behaviors.combat.group.combat_group_behavior import CombatGroupBehavior
from ares.behaviors.combat.individual import KeepUnitSafe, ShootTargetInRange
from ares.managers.manager_mediator import ManagerMediator

if TYPE_CHECKING:
    from ares import AresBot


@dataclass
class KeepGroupSafe(CombatGroupBehavior):
    """A-Move group to a target.

    Example:
    ```py
    from ares.behaviors.combat.group import AMoveGroup

    self.register_behavior(AMoveGroup(units, self.game_info.map_center))
    ```

    Attributes
    ----------
    group : list[Unit]
        Units we want to control.
    close_enemy : Union[Units, list[Unit]]
        Nearby enemy.
    grid : np.ndarray
        Grid we should check for safety.
    attack_in_range_enemy : bool (default=True)
        Attack in range if weapon is ready.
    """

    group: list[Unit]
    close_enemy: Union[Units, list[Unit]]
    grid: np.ndarray
    attack_in_range_enemy: bool = True

    def execute(self, ai: "AresBot", config: dict, mediator: ManagerMediator) -> bool:
        if len(self.group) == 0:
            return False

        executed: bool = False
        for u in self.group:
            if self.attack_in_range_enemy:
                if ShootTargetInRange(u, self.close_enemy).execute(
                    ai, config, mediator
                ):
                    continue
            if KeepUnitSafe(u, self.grid).execute(ai, config, mediator):
                executed = True

        return executed
