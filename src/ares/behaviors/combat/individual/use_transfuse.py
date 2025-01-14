from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

from cython_extensions import cy_distance_to
from sc2.ids.ability_id import AbilityId
from sc2.unit import Unit
from sc2.units import Units

from ares.behaviors.combat.individual import UseAbility
from ares.behaviors.combat.individual.combat_individual_behavior import (
    CombatIndividualBehavior,
)
from ares.managers.manager_mediator import ManagerMediator

if TYPE_CHECKING:
    from ares import AresBot


@dataclass
class UseTransfuse(CombatIndividualBehavior):
    """Queen tries to transfuse something

    Attributes:
        unit: The queen that should transfuse.
        targets: Our own units to transfuse.
        extra_range: Look a bit further out of transfuse range?
            Default is 0.0

    """

    unit: Unit
    targets: Union[list[Unit], Units]
    extra_range: float = 0.0

    def execute(
        self, ai: "AresBot", config: dict, mediator: ManagerMediator, **kwargs
    ) -> bool:
        if self.unit.is_using_ability(AbilityId.TRANSFUSION_TRANSFUSION):
            return True

        if AbilityId.TRANSFUSION_TRANSFUSION in self.unit.abilities:
            transfuse_targets: list[Unit] = [
                u
                for u in self.targets
                if u.health_percentage < 0.4
                and cy_distance_to(self.unit.position, u.position)
                < 7.0 + self.unit.radius + u.radius + self.extra_range
                and u.health_max >= 50.0
                and u.tag != self.unit.tag
                and u.tag not in ai.transfused_tags
            ]
            if transfuse_targets:
                ai.transfused_tags.add(transfuse_targets[0].tag)
                return UseAbility(
                    AbilityId.TRANSFUSION_TRANSFUSION,
                    self.unit,
                    transfuse_targets[0],
                ).execute(ai, config, mediator)

        return False
