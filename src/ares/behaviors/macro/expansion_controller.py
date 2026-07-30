from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2

if TYPE_CHECKING:
    from ares import AresBot

from ares.behaviors.macro.macro_behavior import MacroBehavior
from ares.managers.manager_mediator import ManagerMediator


@dataclass
class ExpansionController(MacroBehavior):
    """Manage expanding.

    Examples
    --------
    Example:
    ```py
    from ares.behaviors.macro import ExpansionController

    self.register_behavior(
        ExpansionController(to_count=8, max_pending=2)
    )
    ```

    Attributes
    ----------
    to_count : int
        The target base count.
    can_afford_check : bool = True
        Check if we can afford expansion. Setting this to False
        will allow the worker to move to a location ready to build
        the expansion.
    check_location_is_safe : bool = True
        Check if we don't knowingly expand at a dangerous
        location.
    max_pending : int = 1
        Maximum pending townhalls at any time.
    prioritize : bool = False
        Will return True for this behavior if we can't afford expansion.
    """

    to_count: int
    can_afford_check: bool = True
    check_location_is_safe: bool = True
    max_pending: int = 1
    prioritize: bool = False

    def execute(self, ai: AresBot, config: dict, mediator: ManagerMediator) -> bool:
        # already have enough / or enough pending
        if (
            len([th for th in ai.townhalls if th.is_ready])
            + ai.structure_pending(ai.base_townhall_type)
            >= self.to_count
            or ai.structure_pending(ai.base_townhall_type) >= self.max_pending
            or (
                self.can_afford_check
                and not self.prioritize
                and not ai.can_afford(ai.base_townhall_type)
            )
        ):
            return False

        if location := self._get_next_expansion_location(ai, mediator):
            if worker := mediator.select_worker(target_position=location):
                mediator.build_with_specific_worker(
                    worker=worker, structure_type=ai.base_townhall_type, pos=location
                )
                return True

        return False

    def _get_next_expansion_location(
        self, ai: AresBot, mediator: ManagerMediator
    ) -> Point2 | None:
        grid: np.ndarray = mediator.get_ground_grid
        for el in mediator.get_own_expansions:
            location: Point2 = el[0]
            if (
                (
                    self.check_location_is_safe
                    and not mediator.is_position_safe(grid=grid, position=location)
                )
                or ai.location_is_blocked(mediator, location)
                or not mediator.can_place_structure(
                    position=location, structure_type=UnitTypeId.COMMANDCENTER
                )
            ):
                continue

            return location

        return None
