from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
from cython_extensions import cy_distance_to_squared
from cython_extensions.geometry import cy_towards
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId as UnitID
from sc2.position import Point2
from sc2.unit import Unit

from ares.behaviors.combat.individual import CombatIndividualBehavior, KeepUnitSafe
from ares.managers.manager_mediator import ManagerMediator

if TYPE_CHECKING:
    from ares import AresBot


@dataclass
class QueenSpreadCreep(CombatIndividualBehavior):
    """Attempt to spread creep along a path, from
    `start` to `target`.

    Example:
    ```py
    from ares.behaviors.combat.individual import QueenSpreadCreep

    target: Point2 = self.ai.enemy_start_locations[0]
    self.register_behavior(QueenSpreadCreep(queen, queen.position, target))
    ```

    Attributes:
        unit: Unit
        cancel_if_close_enemy: if on route to spread creep,
            and queen in danger.
        pre_move_queen_to_tumor: move queen to tumor placement even
            if not enough energy to spread creep.
    """

    unit: Unit
    cancel_if_close_enemy: bool = True
    pre_move_queen_to_tumor: bool = True

    def execute(self, ai: "AresBot", config: dict, mediator: ManagerMediator) -> bool:
        spreading: bool = self.unit.is_using_ability(AbilityId.BUILD_CREEPTUMOR)
        grid: np.ndarray = mediator.get_cached_ground_grid
        if spreading and (self.cancel_if_close_enemy or self.pre_move_queen_to_tumor):
            return KeepUnitSafe(self.unit, grid).execute(ai, config, mediator)

        # queen already spreading creep, leave alone
        if spreading and not [
            u
            for u in mediator.get_own_structures_dict[UnitID.CREEPTUMORQUEEN]
            if cy_distance_to_squared(self.unit.order_target, u.position) < 3.0
        ]:
            return True

        ability_available: bool = (
            AbilityId.BUILD_CREEPTUMOR_QUEEN in self.unit.abilities
        )
        edge_position: Point2 = mediator.find_nearby_creep_edge_position(
            position=self.unit.position, search_radius=200.0
        )
        if not ability_available:
            if (
                edge_position
                and self.pre_move_queen_to_tumor
                and cy_distance_to_squared(self.unit.position, edge_position) > 9.0
            ):
                self.unit.move(edge_position)
                return True
            return False

        creep_spot: Point2 | None = None
        if edge_position and mediator.get_creep_coverage > 20.0:
            creep_spot = edge_position
        elif tumor_placement := mediator.get_next_tumor_on_path(
            grid=grid,
            from_pos=self.unit.position,
            to_pos=ai.game_info.map_center,
            find_alternative=True,
        ):
            creep_spot = tumor_placement

        if creep_spot:
            if cy_distance_to_squared(self.unit.position, creep_spot) > 25.0:
                self.unit.move(creep_spot)
            else:
                self.unit(AbilityId.BUILD_CREEPTUMOR_QUEEN, creep_spot)
            return True

        return False
