from dataclasses import dataclass
from typing import TYPE_CHECKING

from cython_extensions import (
    cy_attack_ready,
    cy_closest_to,
    cy_distance_to_squared,
    cy_towards,
)
from cython_extensions.units_utils import cy_center
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units

from ares.behaviors.combat.individual import AttackTarget
from ares.behaviors.combat.individual.combat_individual_behavior import (
    CombatIndividualBehavior,
)
from ares.consts import COMMON_UNIT_IGNORE_TYPES, UnitTreeQueryType
from ares.managers.manager_mediator import ManagerMediator

if TYPE_CHECKING:
    from ares import AresBot


@dataclass
class WorkerKiteBack(CombatIndividualBehavior):
    """Shoot at the target if possible, else move back.

    This is similar to stutter unit back, but takes advantage of
    mineral walking.

    Example:
    ```py
    from ares.behaviors.combat.individual import WorkerKiteBack

    unit: Unit
    target: Unit
    self.register_behavior(
        WorkerKiteBack(
            unit, target
        )
    )
    ```

    Attributes:
        unit: The unit to shoot.
        target: The unit we want to shoot at.
        should_attack: Whether to attack `target`. If False, will always try to retreat
        retreat_pathing: Precomputed pathing for retreat
    """

    unit: Unit
    target: Unit
    should_attack: bool = True

    def execute(
        self, ai: "AresBot", config: dict, mediator: ManagerMediator, **kwargs
    ) -> bool:
        unit = self.unit
        target = self.target
        if (
            self.should_attack
            and not target.is_memory
            and cy_attack_ready(ai, unit, target)
        ):
            return AttackTarget(unit=unit, target=target).execute(ai, config, mediator)
        elif mfs := ai.mineral_field:
            unit_pos: Point2 = unit.position
            close_ground_enemy: Units = mediator.get_units_in_range(
                start_points=[unit_pos],
                distances=6.5,
                query_tree=UnitTreeQueryType.EnemyGround,
            )[0].filter(lambda u: u.type_id not in COMMON_UNIT_IGNORE_TYPES)
            if close_ground_enemy:
                pos_of_enemy: Point2 = Point2(cy_center(close_ground_enemy))
                # draw a line back behind the worker, and find a mf
                position = cy_towards(pos_of_enemy, unit_pos, 6.0)
                # don't use mfs that are closer to any enemy
                target_mfs = [
                    mf
                    for mf in mfs
                    if cy_distance_to_squared(mf.position, position)
                    < cy_distance_to_squared(mf.position, pos_of_enemy)
                    and cy_distance_to_squared(mf.position, unit_pos) > 16.0
                ]

                if target_mfs:
                    target_mineral: Unit = cy_closest_to(
                        position=unit_pos, units=target_mfs
                    )
                else:
                    target_mineral: Unit = cy_closest_to(
                        position=ai.start_location, units=mfs
                    )
                unit.gather(target_mineral)
            else:
                unit.gather(cy_closest_to(position=ai.start_location, units=mfs))
            return True
