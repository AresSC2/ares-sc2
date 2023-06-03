from typing import Union

from sc2.position import Point2

def cy_distance_to(
    p1: Union[Point2, tuple[float, float]], p2: Union[Point2, tuple[float, float]]
) -> float:
    """Check distance between two Point2 positions.

    cy_distance_to(Point2, Point2)
    157 ns ± 2.69 ns per loop (mean ± std. dev. of 7 runs, 10,000,000 loops each)

    cy_distance_to(unit1.position, unit2.position)
    219 ns ± 10.5 ns per loop (mean ± std. dev. of 7 runs, 1,000,000 loops each)

    Python alternative:

    Point1.distance_to(Point2)
    386 ns ± 2.71 ns per loop (mean ± std. dev. of 7 runs, 1,000,000 loops each)
    unit1.distance_to(unit2)
    583 ns ± 7.89 ns per loop (mean ± std. dev. of 7 runs, 1,000,000 loops each)

    Parameters
    ----------
    p1 :
    p2 :

    Returns
    -------
    float :

    """
    ...
