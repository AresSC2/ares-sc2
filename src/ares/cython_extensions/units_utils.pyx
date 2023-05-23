from cython cimport boundscheck, wraparound

cdef double euclidean_distance_squared(
        (float, float) p1,
        (float, float) p2
):
    return (p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2

@boundscheck(False)
@wraparound(False)
cpdef object cy_closest_to((float, float) position, object units):
    """
    14.9 µs ± 159 ns per loop (mean ± std. dev. of 7 runs, 100,000 loops each)
    
    python-sc2 `units.closest_to` alternative:
    Closest to a Point2:
    301 µs ± 4.34 µs per loop (mean ± std. dev. of 7 runs, 1,000 loops each)
    Closest to a Unit
    115 µs ± 2.25 µs per loop (mean ± std. dev. of 7 runs, 10,000 loops each)
    """
    cdef:
        object closest = units[0]
        double closest_dist = 999.9
        double dist = 0.0
        unsigned int len_units = len(units)
        (float, float) pos

    for i in range(len_units):
        unit = units[i]
        pos = unit.position
        dist = euclidean_distance_squared((pos[0], pos[1]), (position[0], position[1]))
        if dist < closest_dist:
            closest_dist = dist
            closest = unit

    return closest
