from libc.math cimport acos, atan2, fabs, pi, sqrt

from math import cos, sin


cdef (float, float, float) cy_get_line_to_point((int, int) pa, (int, int) pb):
    """Cython version of get_line_between_points"""
    cdef:
        int x1 = pa[0]
        int y1 = pa[1]
        int x2 = pb[0]
        int y2 = pb[1]
        (float, float, float) line
        float slope

    if x1 == x2:
        line = (1, 0, -x1)
    else:
        slope = (y2 - y1) / (x2 - x1)
        line = (-slope, 1, -(y1 - (slope * x1)))
    return line

cpdef double cy_angle_to((float, float) from_pos, (float, float) to_pos):
    """Angle from point to other point in radians"""
    return atan2(to_pos[0] - from_pos[0], to_pos[1] - from_pos[1])

cpdef double cy_angle_diff(double a, double b):
    """Absolute angle difference between 2 angles"""
    if a < 0:
        a += pi * 2
    if b < 0:
        b += pi * 2
    return fabs(a - b)
cpdef double cy_distance_to(
        (double, double) p1,
        (double, double) p2
):
    return ((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2) ** 0.5

cpdef double cy_distance_to_squared(
        (double, double) p1,
        (double, double) p2
):
    return (p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2


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


cpdef double cy_get_angle_between_points((float, float) point_a, (float, float) point_b):
    """Get the angle between two points as if they were vectors from the origin.

    Parameters
    ----------
    point_a :
        One point.
    point_b :
        The other point.

    Returns
    -------
    double :
        The angle between the two points.

    """
    cdef:
        float a_dot_b, a_magnitude, b_magnitude

    a_dot_b = point_a[0] * point_b[0] + point_a[1] * point_b[1]
    a_magnitude = sqrt(point_a[0] ** 2 + point_a[1] ** 2)
    b_magnitude = sqrt(point_b[0] ** 2 + point_b[1] ** 2)

    return acos(a_dot_b / (a_magnitude * b_magnitude))


cpdef double cy_find_average_angle(
        (float, float) start_point, (float, float) reference_point, points
):
    """Find the average angle between the points and the reference point.

    Given a starting point, a reference point, and a list of points, find the average
    angle between the vectors from the starting point to the reference point and the
    starting point to the points.

    Parameters
    ----------
    start_point :
        Origin for the vectors to the other given points.
    reference_point :
        Vector forming one leg of the angle.
    points :
        Points to calculate the angle between relative to the reference point.

    Returns
    -------
    double :
        Average angle in radians between the reference point and the given points.

    """
    cdef:
        float[50] angles
        (float, float) ref_point = reference_point
        float ref_magnitude
        float angle_sum = 0
        float x, y
        (float, float) point
        # iterators
        int angle_idx, point_idx

    ref_point[0] = reference_point[0] - start_point[0]
    ref_point[1] = reference_point[1] - start_point[1]
    ref_magnitude = sqrt(ref_point[0] ** 2 + ref_point[1] ** 2)

    for point_idx in range(len(points)):
        point = points[point_idx]
        x = point[0] - start_point[0]
        y = point[1] - start_point[1]
        if (x, y) == ref_point:
            angle = 0
        else:
            angle = cy_get_angle_between_points((x, y), ref_point)
        angles[point_idx] = angle

    for idx in range(point_idx + 1):
        angle_sum += angles[idx]

    return angle_sum / (point_idx + 1)

cpdef ((float, float, float), (float, float)) cy_find_correct_line(points, base_location):
    """

    Given a list of points and a center point, find if there's a line such that all
    other points are above or below the line. Returns the line in the form
    Ax + By + C = 0 and the point that was used.

    If no such line is found, it returns ((0, 0, 0), <last_point_checked>).    

    Parameters
    ----------
    points :
        Points that need to be on one side of the line.
    base_location :
        Starting point for the line.

    Returns
    -------
    Tuple[Tuple[float, float, float], Tuple[float, float]] :
        First element is the coefficients of Ax + By + C = 0.
        Second element is the point used to form the line.

    """
    cdef:
        float a, b, c, value
        int idx
        (float, float, float) line
        int last_temp_idx = 0
        int positive
        int negative

    if len(points) == 1:
        return cy_get_line_to_point(points[0], base_location), points[0]

    for idx in range(len(points)):
        positive = 0
        negative = 0
        temporary = points.copy()
        start_point = temporary.pop(idx)
        a, b, c = cy_get_line_to_point(base_location, start_point)
        for point_idx in range(len(temporary)):
            value = a * temporary[point_idx][0] + b * temporary[point_idx][1] + c
            if value > 0:
                positive += 1
            elif value < 0:
                negative += 1
            if positive > 0 and negative > 0:
                break
        if positive > 0 and negative > 0:
            continue
        else:
            line = (a, b, c)
            break

    return line, points[idx]

cpdef (float, float) cy_translate_point_along_line((float, float) point, float A_value, float distance):
    cdef:
        float angle
        float x_offset
        float y_offset

    angle = atan2(1, -A_value)
    x_offset = distance * cos(angle)
    y_offset = distance * sin(angle)

    return (point[0] + x_offset, point[1] + y_offset)

