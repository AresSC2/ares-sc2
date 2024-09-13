from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

import numpy as np
from sc2.ids.unit_typeid import UnitTypeId as UnitID
from sc2.position import Point2
from sc2.units import Units

from ares.consts import TOWNHALL_TYPES, UnitTreeQueryType

if TYPE_CHECKING:
    from ares import AresBot

from ares.behaviors.macro.macro_behavior import MacroBehavior
from ares.managers.manager_mediator import ManagerMediator


@dataclass
class ExpansionController(MacroBehavior):
    """Manage expanding.

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
    can_afford_check : bool, optional
        Check we can afford expansion.
        Setting this to False will allow worker to move
        to location ready to build expansion.
        (default is `True`)
    check_location_is_safe : bool, optional
        Check we don't knowingly expand at a dangerous location.
        (default is `True`)
    max_pending : int, optional
        Maximum pending townhalls at any time.
        (default is `1`)
    """

    to_count: int
    can_afford_check: bool = True
    check_location_is_safe: bool = True
    max_pending: int = 1

    def execute(self, ai: "AresBot", config: dict, mediator: ManagerMediator) -> bool:
        # already have enough / or enough pending
        if (
            len([th for th in ai.townhalls if th.is_ready])
            + ai.structure_pending(ai.base_townhall_type)
            >= self.to_count
            or ai.structure_pending(ai.base_townhall_type) >= self.max_pending
            or (self.can_afford_check and not ai.can_afford(ai.base_townhall_type))
        ):
            return False

        if location := self._get_next_expansion_location(mediator):
            if worker := mediator.select_worker(target_position=location):
                mediator.build_with_specific_worker(
                    worker=worker, structure_type=ai.base_townhall_type, pos=location
                )
                return True

        return False

    def _get_next_expansion_location(
        self, mediator: ManagerMediator
    ) -> Optional[Point2]:
        grid: np.ndarray = mediator.get_ground_grid
        for el in mediator.get_own_expansions:
            location: Point2 = el[0]
            if (
                self.check_location_is_safe
                and not mediator.is_position_safe(grid=grid, position=location)
                or self._location_is_blocked(mediator, location)
            ):
                continue

            return location

    @staticmethod
    def _location_is_blocked(mediator: ManagerMediator, position: Point2) -> bool:
        """
        Check if enemy or own townhalls are blocking `position`.

        Parameters
        ----------
        mediator : ManagerMediator
        position : Point2

        Returns
        -------
        bool : True if location is blocked by something.

        """
        # TODO: Not currently an issue, but maybe we should consider rocks
        close_enemy: Units = mediator.get_units_in_range(
            start_points=[position],
            distances=5.5,
            query_tree=UnitTreeQueryType.EnemyGround,
        )[0]

        close_enemy: Units = close_enemy.filter(
            lambda u: u.type_id != UnitID.AUTOTURRET
        )
        if close_enemy:
            return True

        if mediator.get_units_in_range(
            start_points=[position],
            distances=5.5,
            query_tree=UnitTreeQueryType.AllOwn,
        )[0].filter(lambda u: u.type_id in TOWNHALL_TYPES):
            return True

        return False
