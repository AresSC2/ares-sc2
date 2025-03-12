from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
from cython_extensions import (
    cy_closest_to,
    cy_distance_to,
    cy_distance_to_squared,
    cy_is_facing,
)
from sc2.ids.ability_id import AbilityId
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units

from ares.behaviors.combat.individual.combat_individual_behavior import (
    CombatIndividualBehavior,
)
from ares.behaviors.combat.individual.place_predictive_aoe import PlacePredictiveAoE
from ares.behaviors.combat.individual.use_aoe_ability import UseAOEAbility
from ares.consts import ALL_WORKER_TYPES
from ares.dicts.unit_data import UNIT_DATA
from ares.managers.manager_mediator import ManagerMediator

if TYPE_CHECKING:
    from ares import AresBot


@dataclass
class ReaperGrenade(CombatIndividualBehavior):
    """Do reaper grenade.

    Example:
    ```py
    from ares.behaviors.combat.individual import ReaperGrenade

    unit: Unit
    target: Unit
    self.register_behavior(DropCargo(unit, target))
    ```

    Attributes:
        unit: The container unit.
        enemy_units: The enemy units.
        retreat_target: The target position where reaper would retreat.
        grid: The grid used to predicatively place the grenade.
        place_predictive: Whether to predicatively place the grenade.
        reaper_grenade_range: The range at which to use the grenade.

    """

    unit: Unit
    enemy_units: Units | list[Unit]
    retreat_target: Point2
    grid: np.ndarray
    place_predictive: bool = True
    reaper_grenade_range: float = 5.0

    def execute(self, ai: "AresBot", config: dict, mediator: ManagerMediator) -> bool:
        if (
            not self.enemy_units
            or AbilityId.KD8CHARGE_KD8CHARGE not in self.unit.abilities
        ):
            return False

        unit_pos: Point2 = self.unit.position
        targets: list[Unit] = [
            t
            for t in self.enemy_units
            if t.is_visible and not UNIT_DATA[t.type_id]["flying"]
        ]
        if not targets:
            return False

        close_unit: Unit = cy_closest_to(unit_pos, targets)

        # close unit is not chasing reaper, throw aggressive grenade
        if (
            self.place_predictive
            and close_unit.type_id not in ALL_WORKER_TYPES
            and cy_is_facing(self.unit, close_unit, 0.1)
        ):
            if path_to_target := mediator.find_raw_path(
                start=unit_pos,
                target=close_unit.position,
                grid=self.grid,
                sensitivity=1,
            ):

                if PlacePredictiveAoE(
                    unit=self.unit,
                    path=path_to_target[:30],
                    enemy_center_unit=close_unit,
                    aoe_ability=AbilityId.KD8CHARGE_KD8CHARGE,
                    ability_delay=34,
                ).execute(ai, config=config, mediator=mediator):
                    return True

        close_targets: list[Unit] = [
            t
            for t in self.enemy_units
            if cy_distance_to_squared(t.position, close_unit.position) < 20
        ]
        if (
            cy_distance_to(close_unit.position, self.unit.position)
            < self.reaper_grenade_range + close_unit.radius
            and len(close_targets) >= 2
        ):
            if UseAOEAbility(
                unit=self.unit,
                ability_id=AbilityId.KD8CHARGE_KD8CHARGE,
                targets=close_targets,
                min_targets=2,
            ).execute(ai, config, mediator):
                return True

        return False
