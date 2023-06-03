import numpy as np

def cy_is_position_safe(
    grid: np.ndarray, position: tuple[int, int], weight_safety_limit: float
) -> bool:
    """Given a grid of influence, check if the given position is above weight_safety_limit.

    627 ns ± 3.12 ns per loop (mean ± std. dev. of 7 runs, 1,000,000 loops each)

    Python alternative:
    4.02 µs ± 20.4 ns per loop (mean ± std. dev. of 7 runs, 100,000 loops each)

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
