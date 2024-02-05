import numpy as np
from scipy.signal import convolve2d

cimport cython
cimport numpy as np


@cython.boundscheck(False)  # Deactivate bounds checking
@cython.wraparound(False)   # Deactivate negative indexing.
cpdef bint can_place_structure(
    (int, int) building_origin,
    (int, int) building_size,
    const unsigned char[:, :] creep_grid,
    const unsigned char[:, :] placement_grid,
    const unsigned char[:, :] pathing_grid,
    bint avoid_creep = 1,
    bint include_addon = 0
):
    """
    Fast alternative to python-sc2 `can_place`
    # TODO: Test if this works / Fix if it doesn't
    # TODO: Addon check
    # 1.21 µs ± 891 ns per loop (mean ± std. dev. of 1000 runs, 10 loops each)
    """
    cdef:
        unsigned int size_x = building_size[0]
        unsigned int size_y = building_size[1]
        unsigned int x = building_origin[0]
        unsigned int y = building_origin[1]
        unsigned int creep_check = 1 if avoid_creep else 0

    cdef Py_ssize_t i, j
    for i in range(size_y):
        for j in range(size_x):
            if placement_grid[y + j, x + i] == 0:
                return 0
            if creep_grid[y + j, x + i] == creep_check:
                return 0
            if pathing_grid[y + j, x + i] == 0:
                return 0
    return 1

@cython.boundscheck(False)  # Deactivate bounds checking
@cython.wraparound(False)   # Deactivate negative indexing.
cpdef list find_building_locations(
    np.ndarray[np.uint8_t, ndim=2] kernel,
    unsigned int x_stride,
    unsigned int y_stride,
    (unsigned int, unsigned int) x_bounds,
    (unsigned int, unsigned int) y_bounds,
    const unsigned char[:, :] creep_grid,
    const unsigned char[:, :] placement_grid,
    const unsigned char[:, :] pathing_grid,
    const unsigned char[:, :] points_to_avoid_grid,
    unsigned int building_width,
    unsigned int building_height,
    bint avoid_creep = 1
):
    """
    Use a convolution pass to find all possible building locations in an area
    See full docs in `placement_solver.pyi`
    64.8 µs ± 4.05 µs per loop (mean ± std. dev. of 1000 runs, 10 loops each)
    """
    cdef:
        unsigned int _x = 0
        unsigned int _y = 0
        unsigned int valid_idx = 0
        float x, y
        int x_min = x_bounds[0]
        int x_max = x_bounds[1]
        int y_min = y_bounds[0]
        int y_max = y_bounds[1]
        unsigned char[:, :] to_convolve = np.ones((x_max - x_min + 1, y_max - y_min + 1), dtype=np.uint8)
        (float, float) [500] valid_spots
        (float, float) center
        float half_width = building_width / 2
        unsigned int creep_check = 0 if avoid_creep else 1
        unsigned int found_this_many_on_y = 0
        Py_ssize_t i, j

    blocked_y = set()

    for i in range(x_min, x_max + 1):
        for j in range(y_min, y_max + 1):
            if points_to_avoid_grid[j][i] == 0 and creep_grid[j][i] == creep_check and placement_grid[j][i] == 1 and pathing_grid[j][i] == 1:
                to_convolve[i - x_min][j - y_min] = 0

    cdef unsigned char[:, :] result = convolve2d(to_convolve, kernel, mode="valid")

    for i in range(0, result.shape[0], x_stride):
        found_this_many_on_y = 0
        for j in range(0, result.shape[1], y_stride):
            if result[i][j] == 0:
                if j in blocked_y:
                    continue

                found_this_many_on_y += 1
                # idea here is to leave a gap sometimes to prevent stuck units
                if j > 0 and found_this_many_on_y % 4 == 0:
                    blocked_y.add(j)
                    continue

                x = i + x_min + half_width
                y = j + y_min + half_width

                # valid building placement is building center, so add half to x and y
                valid_spots[valid_idx][0] = x
                valid_spots[valid_idx][1] = y
                valid_idx += 1

    if valid_idx == 0:
        return []

    return list(valid_spots)[:valid_idx]

