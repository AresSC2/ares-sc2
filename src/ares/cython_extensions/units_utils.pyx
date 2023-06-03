from cython cimport boundscheck, wraparound
import numpy as np
from sklearn.cluster import DBSCAN
cimport numpy as cnp


cdef double euclidean_distance_squared(
        (float, float) p1,
        (float, float) p2
):
    return (p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2

@boundscheck(False)
@wraparound(False)
cpdef (double, double) cy_center(object units):
    """Returns the central position of all units."""
    cdef:
        unsigned int i = 0
        unsigned int num_units = len(units)
        double sum_x, sum_y = 0.0
        (double, double) position
        object unit

    for i in range(num_units):
        pos = units[i]._proto.pos
        position = (pos.x, pos.y)
        sum_x += position[0]
        sum_y += position[1]

    return (sum_x / num_units, sum_y / num_units)

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

@boundscheck(False)  # turn off bounds-checking for entire function
@wraparound(False)  # turn off negative index wrapping for entire function
cpdef tuple group_by_spatial(
        object units,
        float distance = 0.5,
        unsigned int min_samples = 1
):
    """
    Use DBSCAN to group units. Returns grouped units and the tags of units that were not placed in a group.
    """
    cdef unsigned int num_units = len(units)

    if num_units == 0:
        return [], set()

    cdef:
        cnp.ndarray[cnp.int64_t, ndim = 1] clustering_labels
        cnp.ndarray[cnp.double_t, ndim = 2] vectors = np.empty((num_units, 2), dtype=np.double)
        list groups
        set ungrouped_unit_tags
        int label
        unsigned int index, _index, groups_length, max_range, num_clusters
        (double, double) position
        # array.array groups

    for _index in range(num_units):
        position = units[_index].position
        vectors[_index, 0] = position[0]
        vectors[_index, 1] = position[1]

    clustering_labels = DBSCAN(eps=distance, algorithm='kd_tree', min_samples=min_samples).fit(vectors).labels_
    #num_clusters = len(set(clustering_labels)) - (1 if -1 in clustering_labels else 0)

    groups = []
    # groups = array.array('i', [j for j in range(num_clusters_)])

    max_range = len(clustering_labels)
    ungrouped_unit_tags = set()

    for index in range(max_range):
        unit = units[index]
        label = clustering_labels[index]
        if label == -1:
            # not part of a group
            ungrouped_unit_tags.add(unit.tag)
            continue
        # groups[label].append(unit)
        groups_length = len(groups)
        if label >= groups_length:
            groups.append([unit])
        else:
            groups[label].append(unit)

    return groups, ungrouped_unit_tags
