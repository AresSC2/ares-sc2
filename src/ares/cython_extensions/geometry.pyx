from libc.math cimport sqrt


cpdef double cy_distance_to(
        (float, float) p1,
        (float, float) p2
):
    return ((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2) ** 0.5

cpdef (double, double) cy_towards((double, double) start_pos, (double, double) target_pos, double distance):
    cdef:
        (double, double) vector, displacement, new_pos, normalized_vector
        double magnitude

    # Calculate the vector between the points
    vector = (target_pos[0] - start_pos[0], target_pos[1] - start_pos[1])

    # Normalize the vector
    magnitude = sqrt(vector[0]**2 + vector[1]**2)
    normalized_vector = (vector[0] / magnitude, vector[1] / magnitude)

    # Calculate the displacement vector
    displacement = (normalized_vector[0] * distance, normalized_vector[1] * distance)

    # Calculate the new position
    new_pos = (start_pos[0] + displacement[0], start_pos[1] + displacement[1])

    return new_pos
