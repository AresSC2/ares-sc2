from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

from cython_extensions import cy_attack_ready, cy_in_attack_range, cy_pick_enemy_target
from sc2.unit import Unit
from sc2.units import Units

from ares.behaviors.combat.individual.combat_individual_behavior import (
    CombatIndividualBehavior,
)
from ares.managers.manager_mediator import ManagerMediator

if TYPE_CHECKING:
    from ares import AresBot


@dataclass
class ShootTargetInRange(CombatIndividualBehavior):
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

        targets = [
            t
            for t in self.targets
            if not t.is_cloaked or t.is_cloaked and t.is_revealed
        ]
        in_attack_range: list[Unit] = cy_in_attack_range(
            self.unit, targets, self.extra_range
        )

        if len(in_attack_range) == 0:
            return False

        # idea here is if our unit already has an order to shoot one of these
        # in attack range enemies then we return True but don't issue a
        # new action
        if (
            self.unit.orders
            and len([u for u in in_attack_range if u.tag == self.unit.order_target])
            and self.unit.weapon_cooldown == 0.0
        ):
            return True

        enemy_target: Unit = cy_pick_enemy_target(in_attack_range)

        if cy_attack_ready(ai, self.unit, enemy_target):
            self.unit.attack(enemy_target)
            return True

        return False
