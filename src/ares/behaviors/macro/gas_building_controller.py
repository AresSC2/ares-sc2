from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from cython_extensions import cy_distance_to_squared, cy_sorted_by_distance_to
from sc2.position import Point2
from sc2.units import Units

if TYPE_CHECKING:
    from ares import AresBot
from ares.behaviors.macro.macro_behavior import MacroBehavior
from ares.managers.manager_mediator import ManagerMediator


@dataclass
class GasBuildingController(MacroBehavior):
    """Maintain gas building count.
    Finds an ideal mining worker, and an available geyser.
    Then removes worker from mining records and provides a new role.


    Example:
    ```py
    from ares.behaviors.macro import GasBuildingController

    self.register_behavior(
        GasBuildingController(to_count=len(self.townhalls)*2)
    )
    ```

    Attributes
    ----------
    to_count : int
        How many gas buildings would we like?
    max_pending : int (optional)
        How many gas pending at any time?
    closest_to : Point2 (optional)
        Find available geyser closest to this location.
    """

    to_count: int
    max_pending: int = 1
    closest_to: Optional[Point2] = None

    def execute(self, ai: "AresBot", config: dict, mediator: ManagerMediator) -> bool:
        num_gas: int = (
            len(ai.gas_buildings) + mediator.get_building_counter[ai.gas_type]
        )
        # we have enough gas / building gas then don't attempt behavior
        if (
            num_gas >= self.to_count
            or mediator.get_building_counter[ai.gas_type] >= self.max_pending
            or ai.minerals < 35
        ):
            return False

        existing_gas_buildings: Units = ai.all_gas_buildings
        if available_geysers := [
            u
            for u in ai.vespene_geyser
            if not [
                g
                for g in existing_gas_buildings
                if cy_distance_to_squared(u.position, g.position) < 25.0
            ]
            and [
                th
                for th in ai.townhalls
                if cy_distance_to_squared(u.position, th.position) < 144.0
                and th.build_progress > 0.9
            ]
        ]:
            if not self.closest_to:
                self.closest_to = ai.start_location

            available_geysers = cy_sorted_by_distance_to(
                available_geysers, self.closest_to
            )
            if worker := mediator.select_worker(
                target_position=available_geysers[0], force_close=True
            ):
                mediator.build_with_specific_worker(
                    worker=worker,
                    structure_type=ai.gas_type,
                    pos=available_geysers[0],
                )
                return True

        return False
