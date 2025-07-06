from dataclasses import dataclass
from typing import TYPE_CHECKING

from sc2.ids.ability_id import AbilityId
from sc2.position import Point2
from sc2.unit import Unit

from ares.behaviors.combat.individual import CombatIndividualBehavior
from ares.managers.manager_mediator import ManagerMediator

if TYPE_CHECKING:
    from ares import AresBot


@dataclass
class TumorSpreadCreep(CombatIndividualBehavior):
    """Coordinate tumor spread behavior for creep expansion.

    Strategy:
    1. Try to spread directly to creep edge if within range
    2. If no edges in range, spread in direction furthest from existing tumors
    3. If all else fails, spread to random position within range

    Attributes:
        unit (Unit): The tumor unit executing the tumor creep spread.
        target (Point2): The target point for the tumor placement.
    """

    unit: Unit
    target: Point2

    def execute(self, ai: "AresBot", config: dict, mediator: ManagerMediator) -> bool:
        if AbilityId.BUILD_CREEPTUMOR_TUMOR not in self.unit.abilities:
            return False

        # Strategy 1: Try to spread to nearby creep edges
        if chosen_pos := mediator.find_nearby_creep_edge_position(
            position=self.unit.position,
            search_radius=9.5,
            closest_valid=False,
            spread_dist=2.0,
        ):
            self.unit(AbilityId.BUILD_CREEPTUMOR, chosen_pos)
            return True

        # Strategy 2: Spread in direction furthest from existing tumors
        if position := mediator.get_tumor_influence_lowest_cost_position(
            position=self.unit.position
        ):
            self.unit(AbilityId.BUILD_CREEPTUMOR, position)
            return True

        # Strategy 3: Random placement as fallback
        if random_pos := mediator.get_random_creep_position(
            position=self.unit.position
        ):
            self.unit(AbilityId.BUILD_CREEPTUMOR, random_pos)
            return True

        return False
