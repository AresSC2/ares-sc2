import numpy as np
cimport numpy as cnp
from cython cimport boundscheck, wraparound

@boundscheck(False)
@wraparound(False)
cpdef bint cy_is_position_safe(
    cnp.ndarray[cnp.npy_float32, ndim=2] grid,
    (unsigned int, unsigned int) position,
    double weight_safety_limit = 1.0,
):
    """
    987 ns ± 10.1 ns per loop (mean ± std. dev. of 7 runs, 1,000,000 loops each)
    Python alternative:
    4.66 µs ± 64.8 ns per loop (mean ± std. dev. of 7 runs, 100,000 loops each)
    """
    cdef double weight = 0.0
    weight = grid[position[0], position[1]]
    # np.inf check if drone is pathing near a spore crawler
    return weight == np.inf or weight <= weight_safety_limit
