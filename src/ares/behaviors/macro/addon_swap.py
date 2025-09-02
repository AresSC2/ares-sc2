from dataclasses import dataclass
from typing import TYPE_CHECKING

from sc2.data import Race
from sc2.ids.unit_typeid import UnitTypeId as UnitID
from sc2.unit import Unit

if TYPE_CHECKING:
    from ares import AresBot

from cython_extensions import cy_sorted_by_distance_to

from ares.behaviors.macro.macro_behavior import MacroBehavior
from ares.consts import ADD_ONS, ALL_STRUCTURES
from ares.managers.manager_mediator import ManagerMediator

ADDON_TYPES: set[UnitID] = {UnitID.TECHLAB, UnitID.REACTOR}
REACTOR_TYPES: set[UnitID] = {
    UnitID.BARRACKSREACTOR,
    UnitID.FACTORYREACTOR,
    UnitID.STARPORTREACTOR,
}


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

    Attributes:
        structure_needing_addon: The structure type we want the addon for.
        addon_required: Type of addon required.
    """

    structure_needing_addon: Unit | UnitID
    addon_required: UnitID
    precise_addon_structure_id: UnitID | None = None

    def execute(self, ai: "AresBot", config: dict, mediator: ManagerMediator) -> bool:
        assert ai.race == Race.Terran, "Can only swap addons with Terran."
        # check if user provided a precise addon into addon_required
        if self.addon_required not in ADDON_TYPES:
            assert (
                self.addon_required in ADD_ONS
            ), f"Invalid addon type: {self.addon_required}"
            self.precise_addon_structure_id = self.addon_required
            if self.addon_required in REACTOR_TYPES:
                self.addon_required = UnitID.REACTOR
            else:
                self.addon_required = UnitID.TECHLAB
        else:
            assert (
                self.addon_required in ADDON_TYPES
            ), f"`self.addon_required` should be one of {ADDON_TYPES}"

        if isinstance(self.structure_needing_addon, UnitID):
            assert (
                self.structure_needing_addon in ALL_STRUCTURES
            ), f"structure_needing_addon should be one of {ALL_STRUCTURES}"
            structures: list[Unit] = [
                s
                for s in mediator.get_own_structures_dict[self.structure_needing_addon]
                if s.is_ready and not s.has_add_on
            ]
            if len(structures) == 0:
                return False

            self.structure_needing_addon = structures[0]

        if self.structure_needing_addon.build_progress < 1.0:
            return False

        search_for_tags: set[int] = (
            ai.reactor_tags
            if self.addon_required == UnitID.REACTOR
            else ai.techlab_tags
        )

        # search for addon required
        if self.precise_addon_structure_id:
            add_ons: list[Unit] = [
                s
                for s in ai.structures
                if s.type_id == self.precise_addon_structure_id
                and s.tag in search_for_tags
            ]
        else:
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
