from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
from sc2.ids.unit_typeid import UnitTypeId as UnitID
from sc2.position import Point2
from sc2.unit import Unit

if TYPE_CHECKING:
    from ares import AresBot

from cython_extensions import (
    cy_can_place_structure,
    cy_distance_to_squared,
    cy_pylon_matrix_covers,
)

from ares.behaviors.macro.build_structure import BuildStructure
from ares.behaviors.macro.macro_behavior import MacroBehavior
from ares.consts import ID, REQUIRE_POWER_STRUCTURE_TYPES, TARGET, BuildingSize
from ares.managers.manager_mediator import ManagerMediator

PYLON_POWERED_DISTANCE_SQUARED: float = 42.25


@dataclass
class RestorePower(MacroBehavior):
    """Restore power for protoss structures.

    Note: `ProductionController` is set to call this automatically
    configured via `should_repower_structures` parameter.
    Though this behavior may also be used separately.

    Example:
    ```py
    from ares.behaviors.restore_power import RestorePower

    self.register_behavior(RestorePower())
    ```
    """

    def execute(self, ai: "AresBot", config: dict, mediator: ManagerMediator) -> bool:
        if structures_no_power := [
            s
            for s in ai.structures
            if s.type_id in REQUIRE_POWER_STRUCTURE_TYPES
            and not cy_pylon_matrix_covers(
                s.position,
                mediator.get_own_structures_dict[UnitID.PYLON],
                ai.game_info.terrain_height.data_numpy,
                pylon_build_progress=1e-16,
            )
        ]:
            for structure in structures_no_power:
                if self._already_restoring(structure, mediator):
                    continue

                if self._restoring_power(structure, ai, config, mediator):
                    return True

        return False

    @staticmethod
    def _already_restoring(structure: Unit, mediator: ManagerMediator) -> bool:
        """
        Check if unpowered `structure` is currently being restored.
        Potentially probe already on the way?

        Parameters
        ----------
        structure
        mediator

        Returns
        -------

        """
        building_tracker: dict = mediator.get_building_tracker_dict
        for tag, building_info in building_tracker.items():
            type_id: UnitID = building_info[ID]
            if type_id == UnitID.PYLON:
                pos: Point2 = building_info[TARGET]
                if (
                    cy_distance_to_squared(structure.position, pos)
                    < PYLON_POWERED_DISTANCE_SQUARED
                ):
                    return True

        return False

    @staticmethod
    def _restoring_power(
        structure: Unit, ai: "AresBot", config: dict, mediator: ManagerMediator
    ) -> bool:
        """Given an unpowered structure, find a pylon position.

        Parameters
        ----------
        structure
        ai
        mediator

        Returns
        -------

        """
        placements_dict: dict = mediator.get_placements_dict
        position: Point2 = structure.position
        size: BuildingSize = BuildingSize.TWO_BY_TWO
        offset: float = 1.0

        for base_loc, placements_info in placements_dict.items():
            two_by_twos = placements_info[size]
            if available := [
                placement
                for placement in two_by_twos
                if two_by_twos[placement]["available"]
                and cy_distance_to_squared(placement, position)
                < PYLON_POWERED_DISTANCE_SQUARED
                and not two_by_twos[placement]["worker_on_route"]
                and cy_can_place_structure(
                    (placement[0] - offset, placement[1] - offset),
                    (2, 2),
                    ai.state.creep.data_numpy,
                    ai.game_info.placement_grid.data_numpy,
                    mediator.get_ground_grid.astype(np.uint8).T,
                    avoid_creep=True,
                    include_addon=False,
                )
            ]:
                return BuildStructure(
                    base_loc, UnitID.PYLON, closest_to=available[0], wall=True
                ).execute(ai, config, mediator)

        return False
