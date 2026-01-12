from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

from cython_extensions import cy_closer_than
from sc2.data import Race
from sc2.ids.ability_id import AbilityId
from sc2.unit import Unit

from ares.behaviors.combat.individual import UseAOEAbility
from ares.behaviors.combat.individual.combat_individual_behavior import (
    CombatIndividualBehavior,
)
from ares.dicts.aoe_ability_to_range import AOE_ABILITY_SPELLS_INFO
from ares.managers.manager_mediator import ManagerMediator

if TYPE_CHECKING:
    from ares import AresBot


@dataclass
class AutoUseAOEAbility(CombatIndividualBehavior):
    """Pass in a unit and it will find an AOE to use
        and cast it.

    Attributes:
        unit: The unit that potentially has an AOE ability.
        targets: The targets we want to hit.
        min_targets: Minimum targets to hit with spell.
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
    targets: list[Unit]
    bonus_tags: Optional[set] = field(default_factory=set)
    recalculate: bool = False
    stack_same_spell: bool = False

    def execute(self, ai: "AresBot", config: dict, mediator: ManagerMediator) -> bool:
        _abilities: set[AbilityId] = self.unit.abilities
        for ability in AOE_ABILITY_SPELLS_INFO:
            if ability not in _abilities:
                continue

            ability_range: float = (
                AOE_ABILITY_SPELLS_INFO[ability]["range"] + self.unit.radius + 0.5
            )
            _targets: list[Unit] = cy_closer_than(
                self.targets, ability_range, self.unit.position
            )

            if ability == AbilityId.EMP_EMP:
                _targets = [t for t in _targets if t.shield > 48 or t.energy > 48]
            if _targets:
                min_targets: int = 4
                if ability in {
                    AbilityId.EFFECT_CORROSIVEBILE,
                    AbilityId.KD8CHARGE_KD8CHARGE,
                }:
                    min_targets = 1
                elif ability in {AbilityId.EMP_EMP} and ai.enemy_race != Race.Protoss:
                    min_targets = 2

                avoid_own_ground: bool = ability in {
                    AbilityId.KD8CHARGE_KD8CHARGE,
                    AbilityId.PSISTORM_PSISTORM,
                }
                avoid_own_flying: bool = ability in {AbilityId.PSISTORM_PSISTORM}
                return UseAOEAbility(
                    self.unit,
                    ability,
                    _targets,
                    min_targets=min_targets,
                    avoid_own_ground=avoid_own_ground,
                    avoid_own_flying=avoid_own_flying,
                    bonus_tags=self.bonus_tags,
                    recalculate=self.recalculate,
                    stack_same_spell=self.stack_same_spell,
                ).execute(ai, config, mediator)
        return False
