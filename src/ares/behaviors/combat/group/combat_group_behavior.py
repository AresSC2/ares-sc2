from typing import TYPE_CHECKING, Protocol, Union

from cython_extensions import cy_distance_to_squared
from sc2.ids.ability_id import AbilityId
from sc2.position import Point2
from sc2.unit import Unit

from ares.behaviors.behavior import Behavior
from ares.managers.manager_mediator import ManagerMediator

if TYPE_CHECKING:
    from ares import AresBot


class CombatGroupBehavior(Behavior, Protocol):
    """Interface that all group combat behaviors should adhere to."""

    def execute(self, ai: "AresBot", config: dict, mediator: ManagerMediator) -> bool:
        """Execute the implemented behavior.

        Parameters
        ----------
        ai :
            Bot object that will be running the game.
        config :
            Dictionary with the data from the configuration file.
        mediator :
            ManagerMediator used for getting information from other managers.

        Returns
        ----------
        bool :
            CombatGroupBehavior carried out an action.
        """
        ...

    def duplicate_or_similar_order(
        self,
        unit: Unit,
        target: Union[Point2, Unit],
        order_type: AbilityId,
        distance_check_squared: float = 2.0,
    ) -> bool:
        if (
            cy_distance_to_squared(unit.position, target.position)
            < distance_check_squared
        ):
            return True

        if order_target := unit.order_target:
            # definitely not the same
            if unit.orders[0].ability.id != order_type:
                return False

            # the pos we calculated is not that different to previous target
            if (
                isinstance(order_target, Point2)
                and order_target.rounded == target.position.rounded
            ):
                return True
            if isinstance(order_target, Unit) and order_target == target:
                return True

        return False

    def group_weapons_on_cooldown(
        self, group: list[Unit], stutter_forward: bool
    ) -> bool:
        avg_weapon_cooldown: float = sum([u.weapon_cooldown for u in group]) / len(
            group
        )
        # all weapons are ready, should stay on attack command
        if avg_weapon_cooldown <= 0.0:
            return False

        if stutter_forward:
            return avg_weapon_cooldown > 2.5
        else:
            return avg_weapon_cooldown > 5.0
