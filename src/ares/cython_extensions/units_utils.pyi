import numpy as np
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units


def cy_closest_to(position: Point2, units: Units) -> Unit:
    """Iterate through `units` to find closest to `position`.

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
