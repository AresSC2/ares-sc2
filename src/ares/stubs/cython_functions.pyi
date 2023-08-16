"""Functions written in Cython to give better performance than Python.

Used primarily for numerical tasks and iteration.

"""

from typing import List, Set, Tuple, Union

import numpy as np
from sc2.position import Point2
from sc2.unit import Unit

def add_neighbors_to_ignore(
    points_to_ignore: List[Union[Point2, Tuple[int, int]]]
) -> Set[Tuple[int, int]]:
    """Given a list of points, add each point's neighbors for ease of ignoring.

    Typically used if a tile needs a 3x3 square centered on it to be blocked out

    Parameters
    ----------
    points_to_ignore :
        List of positions whose neighbors should be returned.

    Returns
    -------
    Set[Tuple[int, int]] :
        Set of points that neighbor at least one point in `points_to_ignore`

    """
    ...

def add_units_to_ignore(
    units_to_avoid: List[Unit],
) -> Set[Tuple[int, int]]:
    """Given a list of units, add each unit's position's neighbors for ease of ignoring.

    Typically used if a unit needs a 3x3 square centered on it to be blocked out

    Parameters
    ----------
    units_to_avoid :
        List of `Unit`s whose neighboring tiles should be returned

    Returns
    -------
        Set of points that neighbor at least one unit in `units_to_avoid`
    """
    ...

def all_points_below_max_value(
    grid: np.ndarray,
    max_value: float,
    points_to_check: List[Union[Point2, Tuple[int, int], List[int]]],
) -> bool:
    """Checks whether every point has a value on the grid equal to or below the maximum value.

    Parameters
    ----------
    grid :
        The grid to check.
    max_value :
        The highest value that any point in the grid is allowed to have.
    points_to_check :
        The points in the grid that should be checked.

    Returns
    -------
    bool :
        True if every point checked has a value equal to or lesser than `max_value`,
        False otherwise

    """
    ...

def all_points_have_value(
    grid: np.ndarray, value: int, points: List[Union[List[int], Tuple[int, int]]]
) -> bool:
    """Checks whether every point's value on the grid matches the desired value.

    Parameters
    ----------
    grid :
        The grid to check.
    value :
        The desired value for each point to have.
    points :
        The points in the grid that should be checked.

    Returns
    -------
    bool :
        True if every point checked has the desired value, False otherwise.

    """
    ...

def get_bounding_box(
    coordinates: set[Union[Point2, List[float], Tuple[float, float]]]
) -> Tuple[Tuple[float, float], Tuple[float, float]]:
    """Given a list of coordinates, find a rectangle such that all points are contained in it.

    The rectangle will have its sides parallel to the respective vertical and
    horizontal axes.

    Parameters
    ----------
    coordinates :
        List of coordinates the box should be formed around.

    Returns
    -------
    Tuple[Tuple[float, float], Tuple[float, float]] :
        A tuple of tuples containing ((xmin, xmax), (ymin, ymax))

    """
    ...

def get_neighbors8(
    point: Union[Point2, List[float], Tuple[float, float]]
) -> Set[Tuple[float, float]]:
    """Get the 8 neighboring tiles of a single point.

    Parameters
    ----------
    point :
        The point to get the neighbors of

    Returns
    -------
    Set[Tuple[float, float]] :
        Set of the 8 tiles that are adjacent to the given point.

    """
    ...

def last_index_with_value(
    grid: np.ndarray, value: int, points: List[Union[List[int], Tuple[int, int]]]
) -> int:
    """Finds the index of the last point in `points` where `grid[point] == value`

    Iterates over `points`, stopping as soon as a value doesn't match.

    Parameters
    ----------
    grid :
        Grid to check the value of points in
    value :
        What value the points in the grid should have
    points :
        Which points should be checked in the grid

    Returns
    -------
    int :
        The index of the last point that has the desired value. Returns -1 if points is
        empty or the first value doesn't match.

    """
    ...

def points_with_value(
    grid: np.ndarray, value: int, points: List[Tuple[int, int]]
) -> List[Tuple[int, int]]:
    """Return all points from a grid that match a given value.

    Parameters
    ----------
    grid :
        The grid to check
    value :
        The desired value for points to have in the grid.
    points :
        Which points to check.

    Returns
    -------
    List[Tuple[int, int]] :
        List of points from `points` that have the desired value.

    """
    ...

def translate_point_along_line(
    point: Tuple[float, float], a_value: float, distance: float
) -> Tuple[float, float]:
    """Given a point and slope of a line, translate the point along the line with the
    given slope.

    Parameters
    ----------
    point :
        The point to translate
    a_value :
        A in the equation Ax + y = C (representing the line to translate along)
    distance :
        How far to translate the point

    Returns
    -------
    Tuple[float, float] :
        The translated point

    """
    ...
