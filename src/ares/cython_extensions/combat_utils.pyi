import numpy as np


def cy_is_position_safe(
    grid: np.ndarray, position: tuple[int, int], weight_safety_limit: float
) -> bool:
    """Given a list of points, add each point's neighbors for ease of ignoring.

    Typically used if a tile needs a 3x3 square centered on it to be blocked out

    Parameters
    ----------
    grid :
        2D grid to check with influence.
    position :
        Position converted to x/y integers.
    weight_safety_limit :
        At what threshold is this position deemed unsafe.

    Returns
    -------
    bool :
        This position is safe accoring to weight_safety_limit

    """
    ...
