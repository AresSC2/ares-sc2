from dataclasses import dataclass
from typing import TYPE_CHECKING

from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId as UnitID
from sc2.unit import Unit

if TYPE_CHECKING:
    from ares import AresBot

from ares.behaviors.macro.macro_behavior import MacroBehavior
from ares.managers.manager_mediator import ManagerMediator


@dataclass
class UpgradeCCs(MacroBehavior):
    """Handy behavior for Terran and Protoss.
    Especially combined with `Mining` and ares built in placement solver.
    Finds an ideal mining worker, and an available precalculated placement.
    Then removes worker from mining records and provides a new role.


    Example:
    ```py
    from ares.behaviors.macro import UpgradeCCs

    self.register_behavior(
        UpgradeCCs(to=UnitTypeId.ORBITALCOMMAND, prioritize=True)
    )
    ```

    Attributes:
        to: The structure type we want to build.
        prioritize: If True and there is a CC waiting to upgrade, but
            we can't afford it yet, this behavior will return True
            This is useful in a MacroPlan as it will prevent other
            spending actions occurring.
            Default is False

    """

    to: UnitID
    prioritize: bool = False

    def execute(self, ai: "AresBot", config: dict, mediator: ManagerMediator) -> bool:
        ccs: list[Unit] = [
            th
            for th in mediator.get_own_structures_dict[UnitID.COMMANDCENTER]
            if th.is_ready and th.is_idle
        ]
        # quick exit if no ccs ready
        if not ccs:
            return False

        can_afford: bool = ai.can_afford(self.to)
        can_tech_to: bool = ai.tech_requirement_progress(self.to) == 1.0
        # no ccs or cant afford the upgrade
        if (not self.prioritize and not can_afford) or not can_tech_to:
            return False

        # can't afford, but want to prioritize the upgrade
        # return True so that macro plan doesn't continue
        if not can_afford and self.prioritize:
            return True

        ability: AbilityId = (
            AbilityId.UPGRADETOPLANETARYFORTRESS_PLANETARYFORTRESS
            if self.to == UnitID.PLANETARYFORTRESS
            else AbilityId.UPGRADETOORBITAL_ORBITALCOMMAND
        )
        # we know there are ccs, and we can afford the upgrade
        for cc in ccs:
            cc(ability)
            return True

        return False
