from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

from sc2.ids.ability_id import AbilityId
from sc2.position import Point2
from sc2.unit import Unit

from ares.behaviors.combat.group.combat_group_behavior import CombatGroupBehavior
from ares.managers.manager_mediator import ManagerMediator

if TYPE_CHECKING:
    from ares import AresBot


@dataclass
class GroupUseAbility(CombatGroupBehavior):
    """Issue a single ability command for a group of units.

    Example:
    ```py
    from ares.behaviors.combat.group import GroupUseAbility

    self.register_behavior(
        GroupUseAbility(
            AbilityId.MOVE_MOVE,
            units,
            {u.tag for u in units}
            self.game_info.map_center
        )
    )
    ```

    Attributes
    ----------
    ability: AbilityId
        Ability we want to use.
    group : list[Unit]
        Units we want to control.
    group_tags : set[int]
        The group unit tags.
    target: Union[Point2, Unit, None]
        The target for this ability.
    sync_command: bool (default=True)
        If True, wait for all units to be ready before trying ability
    """

    ability: AbilityId
    group: list[Unit]
    group_tags: set[int]
    target: Union[Point2, Unit]
    sync_command: bool = True

    def execute(self, ai: "AresBot", config: dict, mediator: ManagerMediator) -> bool:
        if len(self.group) == 0:
            return False

        issue_command: bool
        if self.sync_command:
            issue_command = all([self.ability in u.abilities for u in self.group])
        else:
            issue_command = any([self.ability in u.abilities for u in self.group])

        if not issue_command:
            return False

        ai.give_same_action(self.ability, self.group_tags, self.target)
        return True
