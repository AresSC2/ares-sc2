cdef unsigned int euclidean_distance_squared_int(
        (unsigned int, unsigned int) p1,
        (unsigned int, unsigned int) p2
):
    return (p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2

cpdef set flood_fill_grid(
    (unsigned int, unsigned int) start_point,
    const unsigned char[:, :] terrain_grid,
    const unsigned char[:, :] pathing_grid,
    unsigned int max_distance,
    set choke_points
):
    cdef:
        unsigned int terrain_height = terrain_grid[start_point[0], start_point[1]]
        unsigned int pathing_value = pathing_grid[start_point[0], start_point[1]]
        set filled_points = set()

    # Only continue if we can get a height for the starting point
    if not terrain_height:
        return filled_points

    # if pathing_value != 1:
    #     print("r3r3r")
    #     return filled_points

    grid_flood_fill(start_point, terrain_grid, pathing_grid, terrain_height, filled_points, start_point, max_distance, choke_points)
    return filled_points

cdef set grid_flood_fill(
    (unsigned int, unsigned int) point,
    const unsigned char[:, :] terrain_grid,
    const unsigned char[:, :] pathing_grid,
    unsigned int target_val,
    set current_vec,
    (unsigned int, unsigned int) start_point,
    unsigned int max_distance,
    set choke_points):
    cdef:
        unsigned int terrain_height = terrain_grid[start_point[0], start_point[1]]
        unsigned int pathing_value = pathing_grid[start_point[0], start_point[1]]
    # Check that we haven't already added this point.
    if point in current_vec:
        return current_vec

    # Check that this point isn't too far away from the start
    if euclidean_distance_squared_int(point, start_point) > max_distance ** 2:
        return current_vec

    if point in choke_points:
        return current_vec

    terrain_height = terrain_grid[point[0], point[1]]
    pathing_value = pathing_grid[point[0], point[1]]
    if terrain_height != target_val:
        return current_vec

    current_vec.add(point)
    grid_flood_fill((point[0]+1, point[1]), terrain_grid, pathing_grid, terrain_height, current_vec, start_point, max_distance, choke_points)
    grid_flood_fill((point[0]-1, point[1]), terrain_grid, pathing_grid, terrain_height, current_vec, start_point, max_distance, choke_points)
    grid_flood_fill((point[0], point[1]+1), terrain_grid, pathing_grid, terrain_height, current_vec, start_point, max_distance, choke_points)
    grid_flood_fill((point[0], point[1]-1), terrain_grid, pathing_grid, terrain_height, current_vec, start_point, max_distance, choke_points)
