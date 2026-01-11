from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

from cython_extensions import (
    cy_closer_than,
    cy_closest_to,
    cy_distance_to,
    cy_find_aoe_position,
)
from loguru import logger
from sc2.ids.ability_id import AbilityId
from sc2.ids.buff_id import BuffId
from sc2.ids.effect_id import EffectId
from sc2.position import Point2
from sc2.unit import Unit

from ares.behaviors.combat.individual.combat_individual_behavior import (
    CombatIndividualBehavior,
)
from ares.consts import UnitTreeQueryType
from ares.dicts.aoe_ability_to_range import AOE_ABILITY_SPELLS_INFO
from ares.dicts.unit_data import UNIT_DATA
from ares.managers.manager_mediator import ManagerMediator

if TYPE_CHECKING:
    from ares import AresBot


@dataclass
class UseAOEAbility(CombatIndividualBehavior):
    """Attempt to use AOE ability for a unit.

    Attributes:
        unit: The unit that potentially has an AOE ability.
        ability_id: Ability we want to use.
        targets: The targets we want to hit.
        min_targets: Minimum targets to hit with spell.
        avoid_own_flying: Avoid own flying with this spell?
            Default is False.
        avoid_own_ground: Avoid own ground with this spell?
            Default is False.
        bonus_tags: Give more emphasize on this unit tags.
            For example, perhaps a ravager can do corrosive bile
            Provide enemy tags that are currently fungaled?
            Default is empty `Set`
        recalculate: If unit is already using ability, should
            we recalculate this behavior?
            WARNING: could have performance impact
            Default is False.
        stack_same_spell: Stack spell in same position?
            Default is False.

    """

    unit: Unit
    ability_id: AbilityId
    targets: list[Unit]
    min_targets: int
    avoid_own_flying: bool = False
    avoid_own_ground: bool = False
    bonus_tags: Optional[set] = field(default_factory=set)
    recalculate: bool = False
    stack_same_spell: bool = False

    def execute(self, ai: "AresBot", config: dict, mediator: ManagerMediator) -> bool:
        if self.ability_id not in AOE_ABILITY_SPELLS_INFO:
            logger.warning(
                f"You're trying to use {self.ability_id} with `UseAOEAbility`, "
                f"but this behavior doesn't support it"
            )
            return False

        radius: float = AOE_ABILITY_SPELLS_INFO[self.ability_id]["radius"]
        # prevent computation if unit is going to use ability
        if (
            not self.recalculate
            and self.unit.is_using_ability(self.ability_id)
            and self._can_cast(ai, mediator, self.unit.order_target, radius)
        ):
            return True

        # no targets / ability not ready / or
        # total targets not enough / or not valid ability id
        if (
            not self.targets
            or self.ability_id not in self.unit.abilities
            or len(self.targets) < self.min_targets
        ):
            return False

        position = Point2(
            cy_find_aoe_position(
                radius, self.targets, self.min_targets, self.bonus_tags
            )
        )

        if self._can_cast(ai, mediator, position, radius):
            # need to cast on the actual unit
            if self.ability_id in {
                AbilityId.PARASITICBOMB_PARASITICBOMB,
                AbilityId.EFFECT_ANTIARMORMISSILE,
            }:
                self.unit(self.ability_id, cy_closest_to(position, self.targets))
            else:
                self.unit(self.ability_id, position)

            return True
        return False

    def _can_cast(
        self, ai: "AresBot", mediator: ManagerMediator, position: Point2, radius: float
    ) -> bool:
        can_cast: bool = (
            len(cy_closer_than(self.targets, radius, position)) >= self.min_targets
        )
        # check for friendly splash damage
        if can_cast and self.avoid_own_ground or self.avoid_own_flying:
            own_in_range = mediator.get_units_in_range(
                start_points=[position],
                distances=radius,
                query_tree=UnitTreeQueryType.AllOwn,
            )[0]
            if self.avoid_own_flying and [
                u for u in own_in_range if UNIT_DATA[u.type_id]["flying"]
            ]:
                can_cast = False
            elif self.avoid_own_ground and [
                u for u in own_in_range if not UNIT_DATA[u.type_id]["flying"]
            ]:
                can_cast = False

        # check if spell already active in this area
        if (
            not self.stack_same_spell
            and can_cast
            and (effect_or_buff := AOE_ABILITY_SPELLS_INFO[self.ability_id]["effect"])
        ):
            if isinstance(effect_or_buff, EffectId):
                radius: float = AOE_ABILITY_SPELLS_INFO[self.ability_id]["radius"]
                for eff in ai.state.effects:
                    if eff == effect_or_buff and any(
                        [
                            p
                            for p in eff.positions
                            if cy_distance_to(position, p) < radius
                        ]
                    ):
                        can_cast = False
            elif isinstance(effect_or_buff, BuffId):
                if len([u for u in self.targets if u.has_buff(effect_or_buff)]) > 0:
                    can_cast = False

        return can_cast
