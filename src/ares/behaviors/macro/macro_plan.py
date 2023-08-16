from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ares.behaviors.behavior import Behavior
from ares.behaviors.macro import MacroBehavior
from ares.managers.manager_mediator import ManagerMediator

if TYPE_CHECKING:
    from ares import AresBot


@dataclass
class MacroPlan(Behavior):
    """Execute macro behaviors sequentially.

    Idea here is to put macro behaviors in priority order.

    Example:
    ```py
    from ares.behaviors.macro import MacroPlan
    from ares.behaviors.macro import (
        AutoSupply,
        Mining
        SpawnController
    )

    # initiate a new MacroPlan
    macro_plan: MacroPlan = MacroPlan()

    # then add behaviors in the order they should be executed
    macro_plan.add(AutoSupply())
    macro.plan.add(SpawnController(army_composition_dict=self.army_comp))


    # register the macro plan
    self.ai.register_behavior(macro_plan)
    ```

    Attributes
    ----------
    macros : list[Behavior] (optional, default: [])
        A list of behaviors that should be executed
    """

    macros: list[Behavior] = field(default_factory=list)

    def add(self, behavior: MacroBehavior) -> None:
        self.macros.append(behavior)

    def execute(self, ai: "AresBot", config: dict, mediator: ManagerMediator) -> bool:
        for macro in self.macros:
            if macro.execute(ai, config, mediator):
                # executed a macro behavior
                return True
        # none of the macro behaviors completed, no actions executed
        return False
