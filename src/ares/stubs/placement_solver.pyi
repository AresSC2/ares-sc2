import numpy as np

def can_place_structure(
    building_origin: tuple[int, int],
    building_size: tuple[int, int],
    creep_grid: np.ndarray,
    placement_grid: np.ndarray,
    pathing_grid: np.ndarray,
    avoid_creep: bool,
    include_addon: bool,
) -> bool:
    """Simulate whether a structure can be placed at `building_origin`

    Parameters
    ----------
    building_origin
    building_size
    creep_grid
    placement_grid
    pathing_grid
    avoid_creep
    include_addon

    Returns
    -------

    """
    ...

def find_building_locations(
    kernel: np.ndarray,
    x_stride: int,
    y_stride: int,
    x_bounds: tuple[float, float],
    y_bounds: tuple[float, float],
    creep_grid: np.ndarray,
    placement_grid: np.ndarray,
    pathing_grid: np.ndarray,
    points_to_avoid_grid: np.ndarray,
    building_width: int,
    building_height: int,
    avoid_creep: bool,
) -> list[tuple[int, int]]:
    """Use convolution to find building placements in an area.
    Used by `placement_manager`

    Parameters
    ----------
    kernel
    x_stride
    y_stride
    x_bounds
    y_bounds
    creep_grid
    placement_grid
    pathing_grid
    points_to_avoid_grid
    building_width
    building_height
    avoid_creep

    Returns
    -------

    """
    ...
