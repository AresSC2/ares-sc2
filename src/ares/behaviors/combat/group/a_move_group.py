from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

from sc2.ids.ability_id import AbilityId
from sc2.position import Point2
from sc2.unit import Unit

from ares.behaviors.combat.group.combat_group_behavior import CombatGroupBehavior
from ares.managers.manager_mediator import ManagerMediator
from cython_extensions import cy_sorted_by_distance_to

if TYPE_CHECKING:
    from ares import AresBot


@dataclass
class AMoveGroup(CombatGroupBehavior):
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
    target: Point2
        Where the unit is going.
    """

    group: list[Unit]
    target: Union[Point2, Unit]

    def execute(self, ai: "AresBot", config: dict, mediator: ManagerMediator) -> bool:
        if len(self.group) == 0:
            return False

        sorted_units: list[Unit] = cy_sorted_by_distance_to(
            self.group, self.target, reverse=True
        )
        if self.duplicate_or_similar_order(
            sorted_units[0], self.target, AbilityId.ATTACK
        ):
            return False

        ai.give_same_action(AbilityId.ATTACK, [u.tag for u in self.group], self.target)
        return True
