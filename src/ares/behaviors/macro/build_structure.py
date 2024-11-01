from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from sc2.data import Race
from sc2.ids.unit_typeid import UnitTypeId as UnitID
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units

if TYPE_CHECKING:
    from ares import AresBot
from ares.behaviors.macro.macro_behavior import MacroBehavior
from ares.consts import UnitRole
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

    Attributes
    ----------
    base_location : Point2
        The base location to build near.
    structure_id : UnitTypeId
        The structure type we want to build.
    wall : bool
        Find wall placement if possible.
        (Only main base currently supported)
    closest_to : Point2 (optional)
        Find placement at this base closest to
    select_persistent_builder: bool
        If True we can select the persistent_builder if it's available.
    only_select_persistent_builder: bool
        If True, don't find an alternative worker
    """

    base_location: Point2
    structure_id: UnitID
    wall: bool = False
    closest_to: Optional[Point2] = None
    select_persistent_builder: bool = False
    only_select_persistent_builder: bool = False

    def execute(self, ai: "AresBot", config: dict, mediator: ManagerMediator) -> bool:
        assert (
            ai.race != Race.Zerg
        ), "BuildStructure Behavior not currently supported for Zerg."

        within_psionic_matrix: bool = (
            ai.race == Race.Protoss and self.structure_id != UnitID.PYLON
        )

        if placement := mediator.request_building_placement(
            base_location=self.base_location,
            structure_type=self.structure_id,
            wall=self.wall,
            within_psionic_matrix=within_psionic_matrix,
            closest_to=self.closest_to,
        ):
            if worker := self.select_worker(
                mediator,
                placement=placement,
            ):
                mediator.build_with_specific_worker(
                    worker=worker,
                    structure_type=self.structure_id,
                    pos=placement,
                )
                return True
        return False

    def select_worker(
        self,
        mediator: ManagerMediator,
        placement: Point2,
    ) -> Optional[Unit]:
        """Select a worker to build with."""
        if self.select_persistent_builder:
            persistent_workers: Units = mediator.get_units_from_role(
                role=UnitRole.PERSISTENT_BUILDER
            )
            for worker in persistent_workers:
                if (
                    not worker.is_constructing_scv
                    and worker not in mediator.get_building_tracker_dict
                ):
                    return worker
            if self.only_select_persistent_builder:
                return None
        return mediator.select_worker(target_position=placement, force_close=True)
