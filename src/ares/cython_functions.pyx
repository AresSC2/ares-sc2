import numpy as np
cimport numpy as np
from sklearn.cluster import DBSCAN
from sc2.units import Units
from scipy.signal import convolve2d

from libc.math cimport atan2, cos, floor, round, sin, sqrt

DEF ANGLE_STEP = .314159  # the angle step for iteration in radians

np.import_array()

DEF ANGLE_STEP = .314159  # the angle step for iteration in radians


cpdef add_neighbors_to_ignore(
    points_to_ignore
):
    cdef:
        int current_idx = 0
        int i = 0
        int x = 0
        int y = 0
        (int, int) [1008] all_avoid  # 112 base points, chosen arbitrarily
    
    for i in range(len(points_to_ignore)):
        point = points_to_ignore[i]
        for x in range(-1, 2):
            for y in range(-1, 2):
                all_avoid[current_idx][0] = point[0] + x
                all_avoid[current_idx][1] = point[1] + y
                current_idx += 1
                if current_idx >= 1008:
                    return set(list(all_avoid)[:1008])
    return set(list(all_avoid)[:current_idx])


cpdef add_units_to_ignore(
    units_to_avoid,
):
    cdef:
        int current_idx = 0
        int i, x, y
        (int, int) [1008] all_avoid  # 112 base points, chosen arbitrarily

    for i in range(len(units_to_avoid)):
        point = units_to_avoid[i].position
        for x in range(-1, 2):
            for y in range(-1, 2):
                all_avoid[current_idx][0] = point[0] + x
                all_avoid[current_idx][1] = point[1] + y
                current_idx += 1
                if current_idx >= 1008:
                    return set(list(all_avoid)[:1008])
    return set(list(all_avoid)[:current_idx])


cpdef bint all_points_below_max_value(
    const np.float32_t[:, :] grid,
    np.float32_t max_value,
    points_to_check
):
    cdef:
        int x
        int y
    
    for p in points_to_check:
        x = p[0]
        y = p[1]
        if np.inf > grid[x][y] > max_value:
            return False
    
    return True


cpdef bint all_points_have_value(
    const unsigned char[:, :] grid,
    const unsigned char value,
    points
):
    cdef:
        int x
        int y
    
    if len(points) == 0:
        return False

    for p in points:
        x = p[0]
        y = p[1]
        if grid[y][x] != value:
            return False
    return True


cdef float euclidean_distance_squared_char((unsigned char, unsigned char) p1, (unsigned char, unsigned char) p2):
    return (p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2


cdef float euclidean_distance_squared_float((float, float) p1, (float, float) p2):
    return (p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2


cpdef ((float, float), (float, float)) get_bounding_box(list coordinates):
    cdef:
        float x_min = 9999.0
        float x_max = 0.0
        float x_val = 0.0
        float y_min = 9999.0
        float y_max = 0.0
        float y_val = 0.0
        int start = 0
        int stop = len(coordinates)
    for i in range(start, stop):
        x_val = coordinates[i][0]
        y_val = coordinates[i][1]
        if x_val < x_min:
            x_min = x_val
        if x_val > x_max:
            x_max = x_val
        if y_val < y_min:
            y_min = y_val
        if y_val > y_max:
            y_max = y_val
    return (x_min, x_max), (y_min, y_max)


cpdef get_neighbors8((float, float) point):
    cdef:
        int i, j
        int idx = 0
        double x, y
        (double, double) [8] neighbors

    x = floor(point[0])
    y = floor(point[1])

    for i in range(-1, 2):
        for j in range(-1, 2):
            if i == 0 and j == 0:
                continue
            neighbors[idx] = (x + i, y + j)
            idx += 1
    return set(neighbors)


cpdef tuple group_by_spatial(
    object ai,
    object units,
    float distance = 0.5,
    unsigned int min_samples = 1
):
    """
    Use DBSCAN to group units. Returns grouped units and the tags of units that were not placed in a group.
    """
    if not units:
        return [], set()

    cdef:
        np.ndarray[np.int64_t, ndim = 1] clustering_labels
        np.ndarray[np.double_t, ndim = 2] vectors
        list groups, ungrouped_unit_tags
        int label
        unsigned int index, groups_length, min_range, max_range

    vectors = np.array([[unit.position.x, unit.position.y] for unit in units])
    clustering_labels = DBSCAN(eps=distance, algorithm='kd_tree', min_samples=min_samples).fit(vectors).labels_
    groups = []
    min_range = 0
    max_range = len(clustering_labels)
    ungrouped_unit_tags = []

    for index in range(min_range, max_range):
        unit = units[index]
        label = clustering_labels[index]
        if label == -1:
            # not part of a group
            ungrouped_unit_tags.append(unit.tag)
            continue
        groups_length = len(groups)
        if label >= groups_length:
            groups.append([unit])
        else:
            groups[label].append(unit)

    return [Units(raw, ai) for raw in groups], set(ungrouped_unit_tags)


cpdef int last_index_with_value(
    const unsigned char[:, :] grid,
    const unsigned char value,
    points
):
    cdef:
        int x
        int y
        int last_valid_idx = 0
        int stop_val = len(points)
    
    if stop_val == 0:
        return -1
    
    for last_valid_idx in range(stop_val):
        x = points[last_valid_idx][0]
        y = points[last_valid_idx][1]
        if grid[y][x] != value:
            return last_valid_idx - 1
    return last_valid_idx


cpdef points_with_value(
    const unsigned char[:, :] grid,
    const unsigned char value,
    points,
):
    cdef:
        int i, x, y
        int idx = 0
        (int, int) [2000] valid_points

    for i in range(len(points)):
        x = points[i][0]
        y = points[i][1]
        if grid[y][x] == value:
            valid_points[idx] = (x, y)
            idx += 1
            if idx >= 2000:
                break
    return list(valid_points)[:idx]


cpdef (float, float) translate_point_along_line((float, float) point, float A_value, float distance):
    cdef:
        float angle
        float x_offset
        float y_offset
    
    angle = atan2(1, -A_value)
    x_offset = distance * cos(angle)
    y_offset = distance * sin(angle)
    
    return (point[0] + x_offset, point[1] + y_offset)
