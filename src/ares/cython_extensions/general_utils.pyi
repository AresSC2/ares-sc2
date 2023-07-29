from typing import TYPE_CHECKING, Union

import numpy as np
from sc2.ids.unit_typeid import UnitTypeId as UnitID
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units

if TYPE_CHECKING:
    from ares import AresBot

def cy_pylon_matrix_covers(
    position: Union[Point2, tuple[float, float]],
    pylons: Union[Units, list[Unit]],
    height_grid: np.ndarray,
    pylon_build_progress: float,
) -> bool:
    """Check if a position is powered by a pylon.

    1.85 µs ± 8.72 ns per loop (mean ± std. dev. of 7 runs, 1,000,000 loops each)

    Example:
    `can_place_structure_here: bool = cy_pylon_matrix_covers(
        structure_position, self.structures(UnitTypeId.PYLON), self.game_info.terrain_height.data_numpy
    )`

    Parameters
    ----------
    position :
        Position to check for power.
    pylons :
        The pylons we want to check.
    height_grid :
        Height grid supplied from `python-sc2` as a numpy array.
    pylon_build_progress : Optional (default=1.0)
        If less than 1.0, check near pending pylons.

    Returns
    -------
    bool :
        True if `position` has power.
    """

def cy_unit_pending(ai: "AresBot", unit_type: UnitID) -> int:
    """Check how many unit_type are pending.

    Faster unit specific alternative to `python-sc2`'s `already_pending`

    453 ns ± 9.35 ns per loop (mean ± std. dev. of 7 runs, 1,000,000 loops each)

    Python-sc2 `already_pending` alternative:
    2.82 µs ± 29 ns per loop (mean ± std. dev. of 7 runs, 100,000 loops each)

    Parameters
    ----------
    ai :
        Bot object that will be running the game.
    unit_type :
        Unit type we want to check.

    Returns
    -------
    int :
        How many unit_type are currently building.

    """
    ...
