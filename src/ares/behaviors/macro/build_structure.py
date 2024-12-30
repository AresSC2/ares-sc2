from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from cython_extensions.geometry import cy_distance_to_squared
from sc2.data import Race
from sc2.ids.unit_typeid import UnitTypeId as UnitID
from sc2.position import Point2

from ares.consts import BuildingSize
from ares.dicts.structure_to_building_size import STRUCTURE_TO_BUILDING_SIZE

if TYPE_CHECKING:
    from ares import AresBot

from ares.behaviors.macro.macro_behavior import MacroBehavior
from ares.managers.manager_mediator import ManagerMediator


@dataclass
class BuildStructure(MacroBehavior):
    """Handy behavior for Terran and Protoss.
    Especially combined with `Mining` and ares built in placement solver.
    Finds an ideal mining worker, and an available precalculated placement.
    Then removes worker from mining records and provides a new role.


    Example:
    ```py
    from ares.behaviors.macro import BuildStructure

    self.register_behavior(
        BuildStructure(self.start_location, UnitTypeId.BARRACKS)
    )
    ```

    Attributes:
        base_location: The base location to build near.
        structure_id: The structure type we want to build.
        max_on_route: The max number of workers on route to build this. Defaults to 1.
        first_pylon: Will look for the first pylon in placements dict.
            Defaults to False.
        static_defence: Will look for static defense in placements dict.
            Defaults to False.
        wall: Find wall placement if possible. Only the main base is currently
            supported. Defaults to False.
        closest_to: Find placement at this base closest to the given point. Optional.
        to_count: Prevent going over this amount in total.
            Defaults to 0, turning this check off.
        to_count_per_base: Prevent going over this amount at this base location.
            Defaults to 0, turning this check off.
        tech_progress_check: Check if tech is ready before trying to build.
            Defaults to 0.85; setting it to 0.0 turns this check off.

    """

    base_location: Point2
    structure_id: UnitID
    max_on_route: int = 1
    first_pylon: bool = False
    static_defence: bool = False
    wall: bool = False
    closest_to: Optional[Point2] = None
    to_count: int = 0
    to_count_per_base: int = 0
    tech_progress_check: float = 0.85

    def execute(self, ai: "AresBot", config: dict, mediator: ManagerMediator) -> bool:
        assert (
            ai.race != Race.Zerg
        ), "BuildStructure Behavior not currently supported for Zerg."

        # already enough workers on route to build this
        if (
            ai.not_started_but_in_building_tracker(self.structure_id)
            >= self.max_on_route
        ):
            return False
        # if `to_count` is set, see if there is already enough
        if self.to_count and self._enough_existing(ai, mediator):
            return False
        # if we have enough at this base
        if self.to_count_per_base and self._enough_existing_at_this_base(mediator):
            return False

        # tech progress
        if (
            self.tech_progress_check
            and ai.tech_requirement_progress(self.structure_id)
            < self.tech_progress_check
        ):
            return False

        within_psionic_matrix: bool = (
            ai.race == Race.Protoss and self.structure_id != UnitID.PYLON
        )

        if placement := mediator.request_building_placement(
            base_location=self.base_location,
            structure_type=self.structure_id,
            first_pylon=self.first_pylon,
            static_defence=self.static_defence,
            wall=self.wall,
            within_psionic_matrix=within_psionic_matrix,
            closest_to=self.closest_to,
        ):
            if worker := mediator.select_worker(
                target_position=placement,
                force_close=True,
            ):
                mediator.build_with_specific_worker(
                    worker=worker,
                    structure_type=self.structure_id,
                    pos=placement,
                )
                return True
        return False

    def _enough_existing(self, ai: "AresBot", mediator: ManagerMediator) -> bool:
        existing_structures = mediator.get_own_structures_dict[self.structure_id]
        num_existing: int = len(
            [s for s in existing_structures if s.is_ready]
        ) + ai.structure_pending(self.structure_id)
        return num_existing >= self.to_count

    def _enough_existing_at_this_base(self, mediator: ManagerMediator) -> bool:
        placement_dict: dict = mediator.get_placements_dict
        size: BuildingSize = STRUCTURE_TO_BUILDING_SIZE[self.structure_id]
        potential_placements: dict[Point2:dict] = placement_dict[self.base_location][
            size
        ]
        taken: list[Point2] = [
            placement
            for placement in potential_placements
            if not potential_placements[placement]["available"]
        ]
        num_structures: int = 0
        for t in taken:
            if [
                s
                for s in mediator.get_own_structures_dict[self.structure_id]
                if cy_distance_to_squared(s.position, t) < 9.0
            ]:
                num_structures += 1
        return num_structures >= self.to_count_per_base
