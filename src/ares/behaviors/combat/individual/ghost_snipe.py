from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, Union

from cython_extensions import cy_distance_to_squared
from sc2.data import Race
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId as UnitID
from sc2.unit import Unit
from sc2.units import Units

from ares.behaviors.combat.individual import CombatIndividualBehavior
from ares.consts import ALL_STRUCTURES
from ares.dicts.unit_data import UNIT_DATA
from ares.managers.manager_mediator import ManagerMediator

if TYPE_CHECKING:
    from ares import AresBot


@dataclass
class GhostSnipe(CombatIndividualBehavior):
    """Very opinionated ghost snipe.
    Create own behavior based on this if needed.

    Attributes:
    unit: The ghost.
    close_enemy: All close by allied units we want to heal.
    """

    unit: Unit
    close_enemy: Union[list[Unit], Units]

    def execute(self, ai: "AresBot", config: dict, mediator: ManagerMediator) -> bool:
        if (
            ai.enemy_race != Race.Zerg
            or not self.close_enemy
            or self.unit.type_id != UnitID.GHOST
        ):
            return False

        snipe_ability: AbilityId = AbilityId.EFFECT_GHOSTSNIPE
        ghosts: list[Unit] = mediator.get_own_army_dict[UnitID.GHOST]
        if snipe_ability in self.unit.abilities:
            if target := self.get_snipe_target(ai, ghosts, self.close_enemy):
                self.unit(snipe_ability, target)
                return True

        return False

    def get_snipe_target(
        self, ai: "AresBot", ghosts: list[Unit], units: Units
    ) -> Optional[Unit]:
        max_value: float = 0.0
        target: Optional[Unit] = None

        for unit in units:
            if (
                unit.is_memory
                or unit.type_id in ALL_STRUCTURES
                or cy_distance_to_squared(self.unit.position, unit.position) > 125.0
                or ai.get_terrain_height(unit.position)
                > ai.get_terrain_height(self.unit.position)
            ):
                continue
            already_snipe_in_progress: bool = False
            for g in ghosts:
                if g.order_target and g.order_target == unit.tag:
                    already_snipe_in_progress = True
            if already_snipe_in_progress:
                continue

            value: float = (
                UNIT_DATA[unit.type_id]["minerals"] + UNIT_DATA[unit.type_id]["gas"]
            )
            if value >= 100.0 and value > max_value:
                max_value = value
                target = unit

        return target
