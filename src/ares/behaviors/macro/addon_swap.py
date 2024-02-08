from dataclasses import dataclass
from typing import TYPE_CHECKING

from sc2.data import Race
from sc2.ids.unit_typeid import UnitTypeId as UnitID
from sc2.unit import Unit

if TYPE_CHECKING:
    from ares import AresBot

from cython_extensions import cy_sorted_by_distance_to

from ares.behaviors.macro.macro_behavior import MacroBehavior
from ares.managers.manager_mediator import ManagerMediator

ADDON_TYPES: set[UnitID] = {UnitID.TECHLAB, UnitID.REACTOR}


@dataclass
class AddonSwap(MacroBehavior):
    """For Terran only, swap 3x3 structures.
    Pass in two structures and they will swap positions.

    TODO: Extend this to support an exact swap, ie. swap techlab and reactor


    Example:
    ```py
    from ares.behaviors.macro import AddonSwap

    # factory will find a reactor to fly to, any existing
    # structure will fly to the factory's starting position
    self.register_behavior(
        AddonSwap(factory, UnitID.REACTOR)
    )
    ```

    Attributes
    ----------
    structure_needing_addon : Unit
        The structure type we want the addon for
    addon_required : UnitID
        Type of addon required
    """

    structure_needing_addon: Unit
    addon_required: UnitID

    def execute(self, ai: "AresBot", config: dict, mediator: ManagerMediator) -> bool:
        assert ai.race == Race.Terran, "Can only swap addons with Terran."
        assert (
            self.addon_required in ADDON_TYPES
        ), f"`self.addon_required` should be one of {ADDON_TYPES}"
        assert (
            self.structure_needing_addon.build_progress == 1
        ), "Structure requiring addon is not completed, and therefore can't fly"

        search_for_tags: set[int] = (
            ai.reactor_tags
            if self.addon_required == UnitID.REACTOR
            else ai.techlab_tags
        )

        # search for addon required
        add_ons: list[Unit] = [
            s
            for s in ai.structures
            if s.tag in search_for_tags and s.is_ready and s.is_idle
        ]
        if len(add_ons) == 0:
            return False

        closest_addon: Unit = cy_sorted_by_distance_to(
            add_ons, self.structure_needing_addon.position
        )[0]

        # is structure attached to this addon? then move it to `structure_needing_addon`
        if attached_structures := [
            s for s in ai.structures if s.add_on_tag == closest_addon.tag
        ]:
            mediator.move_structure(
                structure=attached_structures[0],
                target=self.structure_needing_addon.position,
            )

        mediator.move_structure(
            structure=self.structure_needing_addon,
            target=closest_addon.add_on_land_position,
        )

        return True
