from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from loguru import logger
from sc2.data import Race
from sc2.ids.unit_typeid import UnitTypeId as UnitID
from sc2.position import Point2

if TYPE_CHECKING:
    from ares import AresBot

from cython_extensions.geometry import cy_distance_to_squared

from ares.behaviors.macro.build_structure import BuildStructure
from ares.behaviors.macro.macro_behavior import MacroBehavior
from ares.behaviors.macro.tech_up import TechUp
from ares.managers.manager_mediator import ManagerMediator

NEXUS_BASE_DISTANCE_SQ: float = 30.25  # 5.5 ** 2


@dataclass
class ProtossStaticDefence(MacroBehavior):
    """Build protoss static defence at all bases with a Nexus.

    Example:
    ```py
    from ares.behaviors.macro import ProtossStaticDefence

    self.register_behavior(ProtossStaticDefence())
    ```

    Attributes:
        pylons_per_base: Number of pylons to maintain per base.
        photon_cannons_per_base: Number of photon cannons to maintain per base.
        shield_batteries_per_base: Number of shield batteries to maintain per base.
        exclude_base_locations: Base locations to skip when placing defence.
        max_on_route: Max number of workers on route per structure type.
        tech_base_location: Where to build tech requirements (forge/core).
    """

    pylons_per_base: int = 1
    photon_cannons_per_base: int = 1
    shield_batteries_per_base: int = 1
    exclude_base_locations: set[Point2] = field(default_factory=set)
    max_on_route: int = 1
    tech_base_location: Point2 | None = None

    def execute(self, ai: "AresBot", config: dict, mediator: ManagerMediator) -> bool:
        if ai.race != Race.Protoss:
            logger.warning(
                f"{ai.time_formatted}: ProtossStaticDefence only supports Protoss."
            )
            return False

        placements_dict: dict = mediator.get_placements_dict
        if not placements_dict:
            return False

        base_locations: list[Point2] = [
            base
            for base in placements_dict.keys()
            if base not in self.exclude_base_locations
        ]
        if not base_locations:
            return False

        if self._tech_required(ai, config, mediator):
            return True

        bases_with_nexus: set[Point2] = set()
        for nexus in ai.townhalls:
            base_loc: Point2 = min(
                base_locations,
                key=lambda loc: cy_distance_to_squared(loc, nexus.position),
            )
            if (
                cy_distance_to_squared(base_loc, nexus.position)
                <= NEXUS_BASE_DISTANCE_SQ
            ):
                bases_with_nexus.add(base_loc)

        if not bases_with_nexus:
            return False

        for base_loc in bases_with_nexus:
            if self.pylons_per_base > 0:
                if BuildStructure(
                    base_location=base_loc,
                    structure_id=UnitID.PYLON,
                    max_on_route=self.max_on_route,
                    to_count_per_base=self.pylons_per_base,
                    closest_to=base_loc,
                    find_alternative=False,
                    production=False,
                ).execute(ai, config, mediator):
                    return True

            if self.photon_cannons_per_base > 0:
                if BuildStructure(
                    base_location=base_loc,
                    structure_id=UnitID.PHOTONCANNON,
                    max_on_route=self.max_on_route,
                    static_defence=True,
                    to_count_per_base=self.photon_cannons_per_base,
                    closest_to=base_loc,
                    find_alternative=False,
                ).execute(ai, config, mediator):
                    return True

            if self.shield_batteries_per_base > 0:
                if BuildStructure(
                    base_location=base_loc,
                    structure_id=UnitID.SHIELDBATTERY,
                    max_on_route=self.max_on_route,
                    static_defence=True,
                    to_count_per_base=self.shield_batteries_per_base,
                    closest_to=base_loc,
                    find_alternative=False,
                ).execute(ai, config, mediator):
                    return True

        return False

    def _tech_required(
        self, ai: "AresBot", config: dict, mediator: ManagerMediator
    ) -> bool:
        tech_location: Point2 = self.tech_base_location or ai.start_location

        if self.photon_cannons_per_base > 0:
            if ai.tech_requirement_progress(UnitID.PHOTONCANNON) < 1.0:
                return TechUp(UnitID.PHOTONCANNON, tech_location).execute(
                    ai, config, mediator
                )

        if self.shield_batteries_per_base > 0:
            if ai.tech_requirement_progress(UnitID.SHIELDBATTERY) < 1.0:
                return TechUp(UnitID.SHIELDBATTERY, tech_location).execute(
                    ai, config, mediator
                )

        return False
