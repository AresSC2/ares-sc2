from dataclasses import dataclass
from typing import TYPE_CHECKING

from cython_extensions import cy_distance_to_squared
from loguru import logger
from sc2.ids.unit_typeid import UnitTypeId as UnitID
from sc2.position import Point2

from ares.consts import BuildingSize

if TYPE_CHECKING:
    from ares.managers.placement_manager import PlacementManager


@dataclass(slots=True)
class PlacementRequest:
    """Options bag for requesting a building placement.

    Extend this rather than growing the request_building_placement signature.
    """

    first_pylon: bool = False
    static_defence: bool = False
    wall: bool = False
    find_alternative: bool = True
    reserve_placement: bool = True
    within_psionic_matrix: bool = False
    pylon_build_progress: float = 1.0
    closest_to: Point2 | None = None
    supply_depot: bool = False
    production: bool = (False,)
    upgrade_structure: bool = (False,)
    bunker: bool = (False,)
    missile_turret: bool = (False,)
    sensor_tower: bool = False
    reaper_wall: bool = False


class BasePlacementStrategy:
    """Base class for placement selection strategies."""

    def __init__(
        self,
        placement_manager: "PlacementManager",
        request: PlacementRequest,
        structure_type: UnitID,
        building_size: BuildingSize,
    ) -> None:
        self.placement_manager: "PlacementManager" = placement_manager
        self.req: PlacementRequest = request
        self.structure_type = structure_type
        self.building_size = building_size

    def _filter_by_flag(
        self, flag_name: str, available, placements_for_base: dict[Point2, dict]
    ) -> list[Point2]:
        return [a for a in available if placements_for_base[a].get(flag_name, False)]


class PoweredPlacementStrategy(BasePlacementStrategy):
    """Select a placement when a psionic matrix (power) is required."""

    def select(
        self,
        available: list[Point2],
        building_at_base: Point2,
        base_location: Point2,
    ) -> None | Point2:
        build_near: Point2 = building_at_base
        closest_to: Point2 = (
            build_near if not self.req.closest_to else self.req.closest_to
        )
        two_by_twos: dict = self.placement_manager.placements_dict[building_at_base][
            BuildingSize.TWO_BY_TWO
        ]
        placements_for_base: dict[
            Point2, dict
        ] = self.placement_manager.placements_dict[building_at_base][self.building_size]

        if self.req.reaper_wall:
            available_reaper_wall = self._filter_by_flag(
                "reaper_wall", available, placements_for_base
            )
            if available_reaper_wall:
                return min(
                    available_reaper_wall,
                    key=lambda k: cy_distance_to_squared(k, closest_to),
                )

        if self.req.wall:
            requested_flags_at_wall: list[str] = []
            if self.req.static_defence:
                requested_flags_at_wall.append("static_defence")

            if requested_flags_at_wall:
                wall_and_other = [
                    a
                    for a in available
                    if placements_for_base[a].get("is_wall", False)
                    and any(
                        placements_for_base[a].get(flag, False)
                        for flag in requested_flags_at_wall
                    )
                ]
                if wall_and_other:
                    return min(
                        wall_and_other,
                        key=lambda k: cy_distance_to_squared(k, closest_to),
                    )
            else:
                # Fallback: any wall placement
                available_wall = self._filter_by_flag(
                    "is_wall", available, placements_for_base
                )
                if available_wall:
                    return min(
                        available_wall,
                        key=lambda k: cy_distance_to_squared(k, closest_to),
                    )

        # Build near optimal pylon if possible and not overcrowded
        optimal_pylon = [
            a
            for a in two_by_twos
            if self.placement_manager.placements_dict[building_at_base][
                BuildingSize.TWO_BY_TWO
            ][a]["optimal_pylon"]
        ]
        if optimal_pylon:
            potential_build_near: Point2 = optimal_pylon[0]
            three_by_threes: dict = self.placement_manager.placements_dict[
                building_at_base
            ][BuildingSize.THREE_BY_THREE]
            close_to_pylon: list[Point2] = [
                p
                for p in three_by_threes
                if cy_distance_to_squared(p, potential_build_near) < 42.25
            ]
            if len(close_to_pylon) < 4:
                build_near = optimal_pylon[0]

        closest_to: Point2 = (
            base_location
            if not self.req.wall
            else self.placement_manager.ai.main_base_ramp.bottom_center
        )

        final_placement = self.placement_manager._find_placement_near_pylon(
            available, build_near, self.req.pylon_build_progress, closest_to
        )
        if not final_placement:
            logger.warning(f"Can't find placement near pylon near {building_at_base}.")
        return final_placement


class UnpoweredPlacementStrategy(BasePlacementStrategy):
    """Select a placement when power is not required."""

    def select(
        self,
        available: list[Point2],
        building_at_base: Point2,
    ) -> None | Point2:
        placements_for_base: dict[
            Point2, dict
        ] = self.placement_manager.placements_dict[building_at_base][self.building_size]

        closest_to: Point2 = (
            building_at_base if not self.req.closest_to else self.req.closest_to
        )

        if self.req.first_pylon:
            available_first_pylon = self._filter_by_flag(
                "first_pylon", available, placements_for_base
            )
            if available_first_pylon:
                return min(
                    available_first_pylon,
                    key=lambda k: cy_distance_to_squared(k, closest_to),
                )

        if self.req.wall:
            # Prefer placements that satisfy wall plus any other requested flags.
            requested_flags_at_wall: list[str] = []
            if self.req.static_defence:
                requested_flags_at_wall.append("static_defence")
            if self.req.production:
                requested_flags_at_wall.append("production")
            if self.req.supply_depot:
                requested_flags_at_wall.append("supply_depot")
            if self.req.bunker:
                requested_flags_at_wall.append("bunker")
            if self.req.upgrade_structure:
                requested_flags_at_wall.append("upgrade_structure")

            if requested_flags_at_wall:
                wall_and_other = [
                    a
                    for a in available
                    if placements_for_base[a].get("is_wall", False)
                    and any(
                        placements_for_base[a].get(flag, False)
                        for flag in requested_flags_at_wall
                    )
                ]
                if wall_and_other:
                    return min(
                        wall_and_other,
                        key=lambda k: cy_distance_to_squared(k, closest_to),
                    )

            # Fallback: any wall placement, excluding static defense spots for pylons
            available_wall = self._filter_by_flag(
                "is_wall", available, placements_for_base
            )
            if available_wall:
                if self.structure_type == UnitID.PYLON:
                    # Filter out static defense spots for pylons
                    available_wall = [
                        p
                        for p in available_wall
                        if not placements_for_base[p].get("static_defence", False)
                    ]
                    if available_wall:
                        return min(
                            available_wall,
                            key=lambda k: cy_distance_to_squared(k, closest_to),
                        )

                    else:
                        # Fallback: closest among available non-wall positions
                        non_wall_positions = [
                            a
                            for a in available
                            if not placements_for_base[a].get("is_wall", False)
                        ]
                        if non_wall_positions:
                            return min(
                                non_wall_positions,
                                key=lambda k: cy_distance_to_squared(k, closest_to),
                            )
                if available_wall:
                    return min(
                        available_wall,
                        key=lambda k: cy_distance_to_squared(k, closest_to),
                    )
                # Fallback: closest among available non-wall positions
                non_wall_positions = [
                    a
                    for a in available
                    if not placements_for_base[a].get("is_wall", False)
                ]
                if non_wall_positions:
                    return min(
                        non_wall_positions,
                        key=lambda k: cy_distance_to_squared(k, closest_to),
                    )
            # Fallback: closest among all available
            return min(
                available,
                key=lambda k: cy_distance_to_squared(k, closest_to),
            )

        else:
            if self.req.reaper_wall:
                available_reaper_wall = self._filter_by_flag(
                    "reaper_wall", available, placements_for_base
                )
                if available_reaper_wall:
                    return min(
                        available_reaper_wall,
                        key=lambda k: cy_distance_to_squared(k, closest_to),
                    )

            if self.req.static_defence:
                available_static_defence = self._filter_by_flag(
                    "static_defence", available, placements_for_base
                )
                if available_static_defence:
                    return min(
                        available_static_defence,
                        key=lambda k: cy_distance_to_squared(k, closest_to),
                    )

            if self.structure_type == UnitID.PYLON:
                available_opt = self._filter_by_flag(
                    "optimal_pylon", available, placements_for_base
                )
                if available_opt:
                    return min(
                        available_opt,
                        key=lambda k: cy_distance_to_squared(k, closest_to),
                    )

                available_prod = self._filter_by_flag(
                    "production_pylon", available, placements_for_base
                )
                if available_prod:
                    return min(
                        available_prod,
                        key=lambda k: cy_distance_to_squared(k, closest_to),
                    )

            if self.structure_type == UnitID.SUPPLYDEPOT and self.req.supply_depot:
                available_opt = self._filter_by_flag(
                    "supply_depot", available, placements_for_base
                )
                if available_opt:
                    return min(
                        available_opt,
                        key=lambda k: cy_distance_to_squared(k, closest_to),
                    )

            if self.structure_type == UnitID.MISSILETURRET and self.req.missile_turret:
                available_opt = self._filter_by_flag(
                    "missile_turret", available, placements_for_base
                )
                if available_opt:
                    return min(
                        available_opt,
                        key=lambda k: cy_distance_to_squared(k, closest_to),
                    )

            if self.structure_type == UnitID.SENSORTOWER and self.req.sensor_tower:
                available_opt = self._filter_by_flag(
                    "sensor_tower", available, placements_for_base
                )
                if available_opt:
                    return min(
                        available_opt,
                        key=lambda k: cy_distance_to_squared(k, closest_to),
                    )

            if self.req.production:
                available_opt = self._filter_by_flag(
                    "production", available, placements_for_base
                )
                if available_opt:
                    return min(
                        available_opt,
                        key=lambda k: cy_distance_to_squared(k, closest_to),
                    )

        # default choice if nothing else hits
        non_custom = [
            a for a in available if not placements_for_base[a].get("custom", False)
        ]
        if non_custom:
            final_placement: Point2 = min(
                non_custom,
                key=lambda k: cy_distance_to_squared(k, closest_to),
            )
        else:
            final_placement: Point2 = min(
                available,
                key=lambda k: cy_distance_to_squared(k, closest_to),
            )

        return final_placement
