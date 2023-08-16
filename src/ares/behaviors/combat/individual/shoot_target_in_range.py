from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

from sc2.unit import Unit
from sc2.units import Units

from ares.behaviors.combat import CombatBehavior
from ares.cython_extensions.combat_utils import cy_attack_ready, cy_pick_enemy_target
from ares.cython_extensions.units_utils import cy_in_attack_range
from ares.managers.manager_mediator import ManagerMediator

if TYPE_CHECKING:
    from ares import AresBot


@dataclass
class ShootTargetInRange(CombatBehavior):
    """Find something to shoot at.

    TODO: Currently only picks lowest health.
        Might want to pick best one shot KO for example

    Example:
    ```py
    from ares.behaviors.combat import ShootTargetInRange

    unit: Unit
    target: Unit
    self.register_behavior(ShootTargetInRange(unit, target))
    ```

    Attributes
    ----------
    unit: Unit
        The unit to shoot.
    targets : Union[list[Unit], Units]
        Units we want to check.
    extra_range: float (optional)
        Look outside unit weapon range.
        This might be useful for hunting down low hp units.
    """

    unit: Unit
    targets: Union[list[Unit], Units]
    extra_range: float = 0.0

    def execute(
        self, ai: "AresBot", config: dict, mediator: ManagerMediator, **kwargs
    ) -> bool:
        if not self.targets:
            return False

        in_attack_range: list[Unit] = cy_in_attack_range(
            self.unit, self.targets, self.extra_range
        )

        if len(in_attack_range) == 0:
            return False

        enemy_target: Unit = cy_pick_enemy_target(in_attack_range)

        if cy_attack_ready(ai, self.unit, enemy_target):
            self.unit.attack(enemy_target)
            return True

        return False
