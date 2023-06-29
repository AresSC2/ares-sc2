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

def cy_towards(
    start_pos: Point2, target_pos: Point2, distance: float
) -> tuple[float, float]:
    """Get position from start_pos towards target_pos based on distance.

    Note: For performance reasons this returns the point2 as a tuple, if a
    python-sc2 Point2 is required it's up to the user to convert it.
    Example:
    `new_pos: Point2 = Point2(cy_towards(self.start_location, self.enemy_start_locations, 10.0))`

    Though for best performance it is recommended to simply work with the tuple if possible:
    `new_pos: tuple[float, float] = cy_towards(self.start_location, self.enemy_start_locations, 10.0)`

    191 ns ± 0.855 ns per loop (mean ± std. dev. of 7 runs, 10,000,000 loops each)

    Python-sc2's `start_pos.towards(target_pos, distance)` alternative:
    2.73 µs ± 18.9 ns per loop (mean ± std. dev. of 7 runs, 100,000 loops each)


    Parameters
    ----------
    start_pos :
        Start from this 2D position.
    target_pos :
        Go towards this 2D position.
    distance :
        How far we go towards target_pos.

    Returns
    -------
    tuple[float, float] :

    """
    ...
