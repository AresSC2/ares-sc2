from typing import Union

import numpy as np
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units

def cy_center(units: Units) -> tuple[float, float]:
    """
    54.2 µs ± 137 ns per loop (mean ± std. dev. of 7 runs, 10,000 loops each)

    `python-sc2`'s `units.center` alternative:
    107 µs ± 255 ns per loop (mean ± std. dev. of 7 runs, 10,000 loops each)

    Example:
    centroid = Point2(cy_center(self.workers))

    Parameters
    ----------
    units :

    Returns
    -------
    tuple[float, float] :
        Centroid of all units positions
    """
    ...

def cy_closest_to(position: Point2, units: Units) -> Unit:
    """Iterate through `units` to find closest to `position`.

    14.3 µs ± 135 ns per loop (mean ± std. dev. of 7 runs, 100,000 loops each)

    python-sc2's `units.closest_to()` alternative:
    98.9 µs ± 240 ns per loop (mean ± std. dev. of 7 runs, 10,000 loops each)
    If using `units.closest_to(Point2):
    200 µs ± 1.02 µs per loop (mean ± std. dev. of 7 runs, 1,000 loops each)

    Parameters
    ----------
    position :
        Position to measure distance from.
    units :
        Collection of units we want to check.

    Returns
    -------
    Unit :
        Unit closest to `position`.

    """
    ...

def cy_in_attack_range(
    unit: Unit, units: Union[Units, list[Unit]], bonus_distance: float = 0.0
) -> list[Unit]:
    """Find all units that unit can shoot at.

    7.28 µs ± 26.3 ns per loop (mean ± std. dev. of 7 runs, 100,000 loops each)

    python-sc2's `units.in_attack_range_of(unit)` alternative:
    30.4 µs ± 271 ns per loop (mean ± std. dev. of 7 runs, 10,000 loops each)

    Parameters
    ----------
    unit :
        Position to measure distance from.
    units :
        Collection of units we want to check.
    bonus_distance :

    Returns
    -------
    list[Unit] :
        Units that are in attack range of `unit`.

    """
    ...

def group_by_spatial(
    ai: "BotAI", units: "Units", distance: float = 0.5, min_samples: int = 1
) -> tuple[list["Units"], set[int]]:
    """Use DBSCAN to group units. Returns grouped units and the tags of units that
    were not placed in a group.

    Warning:
    Do not spam this function

    See https://scikit-learn.org/stable/modules/generated/sklearn.cluster.DBSCAN.html
    for additional information on distance and min_samples.

    1.25 ms ± 6.92 µs per loop (mean ± std. dev. of 7 runs, 1,000 loops each)
    (DBSCAN takes up most of this time)

    Parameters
    ----------
    ai :
        Bot object used for creating `Units` objects
    units :
        Units to form groups from
    distance :
        DBSCAN eps (essentially the maximum distance between units for them to be
        considered as part of the same group)
    min_samples :
        DBSCAN min_samples (essentially the number of other units that need to be
        around a unit for that unit to start forming a group)

    Returns
    -------
    Tuple[List["Units"], Set[int]] :
        Tuple of:
            List of `Units` objects representing the groups formed
            Set of tags of the `Unit`s that were not placed into a group

    """
    ...

def cy_sorted_by_distance_to(
    units: Union[Units, list[Unit]], position: Point2, reverse: bool = False
) -> list[Unit]:
    """Sort units by distance to `position`

    33.7 µs ± 190 ns per loop (mean ± std. dev. of 7 runs, 10,000 loops each)

    python-sc2's `units.sorted_by_distance_to(position)` alternative:
    246 µs ± 830 ns per loop (mean ± std. dev. of 7 runs, 1,000 loops each)

    Parameters
    ----------
    units :
        Units we want to sort.
    position :
        Sort by distance to this position.
    reverse :
        Not currently used.
    Returns
    -------
    list[Unit] :
        Units sorted by distance to position.

    """
    ...
