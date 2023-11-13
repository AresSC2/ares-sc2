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

        Parameters
        ----------
        unit :
            This is the medivac / prism / overlord
        units_to_transport :
            Units we want to transport.
            This can be an empty list if the units are
            already in the dropship cargo.
        air_grid :
            The airgrid our dropship can path on
        target :
            Where to drop our cargo:
        should_drop_units : Optional
            Drop off units when reaching destination
        keep_dropship_safe : Optional
            Setting this to true will keep dropship safe
            if nothing else to do.
        cargo_switch_to_role : Optional
            When picking up a unit this will switch their role.
            This is useful in that soon as the unit
            is dropped off it will be ready to do its
            new task.
        success_at_distance : Optional
            The pathing behavior will be considered complete
            when this distance from `target`.

        Returns
        -------
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
