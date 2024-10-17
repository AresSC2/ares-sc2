import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

from sc2.data import Race
from sc2.ids.unit_typeid import UnitTypeId as UnitID
from sc2.position import Point2

if TYPE_CHECKING:
    from ares import AresBot

from cython_extensions import cy_unit_pending

from ares.behaviors.macro.build_structure import BuildStructure
from ares.behaviors.macro.macro_behavior import MacroBehavior
from ares.consts import ALL_PRODUCTION_STRUCTURES, RACE_SUPPLY
from ares.managers.manager_mediator import ManagerMediator


@dataclass
class AutoSupply(MacroBehavior):
    """Automatically build supply, works for all races.

    Example:
    ```py
    from ares.behaviors.macro import AutoSupply

    self.register_behavior(AutoSupply(self.start_location))
    ```

    Attributes
    ----------
    base_location : Point2
        The base location where supply should be built.
    return_true_if_supply_required : bool
        Can't afford supply, but it's required, return true?
        Useful if creating a `MacroPlan`

    Returns
    ----------
    bool :
        True if this Behavior carried out an action.
    """

    base_location: Point2
    return_true_if_supply_required: bool = True

    def execute(self, ai: "AresBot", config: dict, mediator: ManagerMediator) -> bool:
        if self._num_supply_required(ai, mediator) > 0:
            supply_type: UnitID = RACE_SUPPLY[ai.race]
            if ai.race == Race.Zerg:
                if ai.num_larva_left > 0 and ai.can_afford(supply_type):
                    ai.train(supply_type)
                    ai.num_larva_left -= 1
                    return True
            else:
                BuildStructure(self.base_location, supply_type).execute(
                    ai, config, mediator
                )
            return self.return_true_if_supply_required

        return False

    @staticmethod
    def _num_supply_required(ai: "AresBot", mediator: ManagerMediator) -> int:
        """
        TODO: Improve on this initial version
            Should calculate based on townhalls for Zerg only?
            Other races should be calculated based on production available
        """
        if ai.supply_cap >= 200:
            return 0

        num_ths: int = len(ai.ready_townhalls)
        supply_left: float = ai.supply_left
        supply_used: float = ai.supply_used
        pending_supply_units: int
        if ai.race == Race.Zerg:
            pending_supply_units = cy_unit_pending(ai, UnitID.OVERLORD)
        else:
            pending_supply_units = (
                int(ai.already_pending(RACE_SUPPLY[ai.race]))
                + mediator.get_building_counter[RACE_SUPPLY[ai.race]]
            )

        # zerg supply focus around townhalls
        if ai.race == Race.Zerg:
            # supply blocked
            if supply_left <= 0 and pending_supply_units < (num_ths + 1):
                max_supply: int = num_ths if supply_used < 72 else num_ths + 1
                return max_supply - pending_supply_units

            # low supply, restrict supply production
            if 60 > supply_used >= 13:
                supply_left_threshold: int = 5 if supply_used <= 36 else 6
                num_building = 1 if supply_left > 0 or supply_used < 29 else 2
                if (
                    supply_left <= supply_left_threshold
                    and pending_supply_units < num_building
                ):
                    return num_building - pending_supply_units
            else:
                if ai.race == Race.Zerg:
                    # scale up based on townhalls
                    if supply_left < 4 * num_ths and pending_supply_units < num_ths:
                        num: int = num_ths - pending_supply_units
                        return min(num, 6)
        # other races supply based on production facilities
        else:
            # scale up based on production structures
            num_production_structures: int = len(
                ai.structures.filter(
                    lambda s: s.type_id in ALL_PRODUCTION_STRUCTURES
                    and s.build_progress == 1.0
                )
            )
            if supply_left <= max(
                2 * num_production_structures, 5
            ) and pending_supply_units < math.ceil(num_production_structures / 2):
                num: int = (
                    math.ceil(num_production_structures / 2) - pending_supply_units
                )
                return min(num, 6)

            # we have no prod structures, just in case
            elif (
                num_production_structures == 0
                and supply_left <= 2
                and not pending_supply_units
            ):
                return 1 - pending_supply_units

        return 0
