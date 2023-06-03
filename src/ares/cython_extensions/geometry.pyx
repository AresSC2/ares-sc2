cpdef double cy_distance_to(
        (float, float) p1,
        (float, float) p2
):
    return ((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2) ** 0.5
