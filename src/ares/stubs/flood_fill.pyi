import numpy as np
from sc2.position import Point2

def flood_fill_grid(
    start_point: Point2,
    terrain_grid: np.ndarray,
    pathing_grid: np.ndarray,
    max_distance: int,
    choke_points: set[Point2],
) -> set[tuple[int, int]]:
    """
    Given a point, flood fill outward from it and return the valid points. Does not continue through chokes.

    Parameters
    ----------
    start_point :
        Start flood fill outwards from this point.
    terrain_grid :
        Terrain grid from python-sc2, make sure this is transposed.
    pathing_grid :
        Pathing grid from MapAnalyzer
        python-sc2 pathing grid may work, but doesn't include rocks etc
    max_distance :
        Distance from start point before finishing the algorithm.
    choke_points :
        Set of choke points to prevent the flood fill spreading through.

    Returns
    -------
        Set of points that are filled in
    """
    ...
