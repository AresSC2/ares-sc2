from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

from cython_extensions import cy_sorted_by_distance_to
from sc2.ids.ability_id import AbilityId
from sc2.position import Point2
from sc2.unit import Unit

from ares.behaviors.combat.group.combat_group_behavior import CombatGroupBehavior
from ares.managers.manager_mediator import ManagerMediator

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
    group_tags : set[int]
        The group unit tags.
    target: Point2
        Where the unit is going.
    """

    group: list[Unit]
    group_tags: set[int]
    target: Union[Point2, Unit]

    def execute(self, ai: "AresBot", config: dict, mediator: ManagerMediator) -> bool:
        if len(self.group) == 0:
            return False

        sorted_units: list[Unit] = cy_sorted_by_distance_to(
            self.group, self.target.position, reverse=True
        )
        if self.duplicate_or_similar_order(
            sorted_units[0], self.target, AbilityId.ATTACK
        ):
            return False

        ai.give_same_action(AbilityId.ATTACK, self.group_tags, self.target)
        return True
