from dataclasses import dataclass
from typing import Optional

import numpy as np
from sc2.position import Point2
from sc2.unit import Unit

from ares.behaviors.combat import CombatManeuver
from ares.behaviors.combat.individual import (
    DropCargo,
    KeepUnitSafe,
    PathUnitToTarget,
    PickUpCargo,
)
from ares.consts import UnitRole


@dataclass
class DropShipRecipes:
    @staticmethod
    def pickup_and_transport_cargo(
        unit: Unit,
        units_to_transport: list[Unit],
        air_grid: np.ndarray,
        target: Point2,
        should_drop_units: bool = True,
        keep_dropship_safe: bool = True,
        cargo_switch_to_role: Optional[UnitRole] = None,
        success_at_distance: float = 2.0,
    ) -> CombatManeuver:
        """
        This is similar to `pickup_transport_and_drop_units`
        But DOES NOT drop off the units

        WARNING: Ensure `units_to_transport` are not already near
        the dropoff point, or this might cause an infinite cycle.

    Parameters:
        unit: The medivac, prism, or overlord.
        units_to_transport: Units to be transported, can be empty
            if they are already in the dropship cargo.
        air_grid: The airgrid for dropship pathing.
        target: The destination for cargo drop.
        should_drop_units: Whether to drop units when reaching the destination.
            Defaults to True
        keep_dropship_safe: If set to True, the dropship will be
            kept safe if no other tasks are present. Defaults to True.
        cargo_switch_to_role: Switch the unit's role when picked up, useful for
            task readiness after drop. Defaults to None.
        success_at_distance: The behavior is complete when the unit is within
            this distance from `target`. Defaults to 2.0.

        """
        maneuver: CombatManeuver = CombatManeuver()
        maneuver.add(
            PickUpCargo(
                unit=unit,
                grid=air_grid,
                pickup_targets=units_to_transport,
                cargo_switch_to_role=cargo_switch_to_role,
            )
        )
        if unit.has_cargo:
            # path to target
            maneuver.add(
                PathUnitToTarget(
                    unit=unit,
                    grid=air_grid,
                    target=target,
                    success_at_distance=success_at_distance,
                )
            )
            if should_drop_units:
                maneuver.add(DropCargo(unit=unit, target=unit.position))
        if keep_dropship_safe:
            maneuver.add(KeepUnitSafe(unit=unit, grid=air_grid))
        return maneuver
