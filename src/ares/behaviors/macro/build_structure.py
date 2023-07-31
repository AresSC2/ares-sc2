from dataclasses import dataclass

from sc2.ids.unit_typeid import UnitTypeId as UnitID
from sc2.data import Race
from sc2.position import Point2
from ares.managers.manager_mediator import ManagerMediator

from ares import AresBot

from ares.behaviors.macro.macro_behavior import MacroBehavior


@dataclass
class BuildStructure(MacroBehavior):
    """Handle worker mining control.

    Note: Could technically be `CombatBehavior`, but is treated here as a
    MacroBehavior since many tasks are carried out.

    Attributes
    ----------
    base_location : Point2
        The base location to build near.
    structure_id : UnitTypeId
        The structure type we want to build.
    wall : bool
        Find wall placement if possible.
        (Only main base currently supported)
    """

    base_location: Point2
    structure_id: UnitID
    wall: bool = False

    def execute(self, ai: "AresBot", config: dict, mediator: ManagerMediator) -> bool:
        assert (
            ai.race != Race.Zerg
        ), "BuildStructure Behavior not currently supported for Zerg."

        within_psionic_matrix: bool = ai.race == Race.Protoss and self.structure_id != UnitID.PYLON

        if placement := mediator.request_building_placement(
            base_location=self.base_location,
            structure_type=self.structure_id,
            wall=self.wall,
            within_psionic_matrix=within_psionic_matrix,
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
