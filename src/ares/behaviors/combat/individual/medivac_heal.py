from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
from cython_extensions import cy_closest_to
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId as UnitID
from sc2.unit import Unit

from ares.behaviors.combat.individual import CombatIndividualBehavior, KeepUnitSafe
from ares.managers.manager_mediator import ManagerMediator

if TYPE_CHECKING:
    from ares import AresBot


@dataclass
class MedivacHeal(CombatIndividualBehavior):
    """Given close allied units, heal things up.

    Attributes:
        unit: The siege tank unit.
        close_allied: All close by allied units we want to heal.
        grid: The path for medivac to heal on
        keep_safe: Attempt to stay safe, this may result in
            not always healing units (Default is True)
    """

    unit: Unit
    close_allied: list[Unit]
    grid: np.ndarray
    keep_safe: bool = True

    def execute(self, ai: "AresBot", config: dict, mediator: ManagerMediator) -> bool:
        if self.unit.type_id != UnitID.MEDIVAC:
            return False

        if self.keep_safe and KeepUnitSafe(self.unit, self.grid).execute(
            ai, config, mediator
        ):
            return True

        # don't interfere
        if self.unit.is_using_ability(AbilityId.MEDIVACHEAL_HEAL):
            return True

        bio_need_healing: list[Unit] = [
            u
            for u in self.close_allied
            if u.is_biological and u.health_percentage < 1.0
        ]
        # found something to heal
        if len(bio_need_healing) > 0:
            target_unit: Unit = cy_closest_to(self.unit.position, bio_need_healing)
            self.unit(AbilityId.MEDIVACHEAL_HEAL, target_unit)
            return True

        return False
