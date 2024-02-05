__version__ = "0.2.0"

# bootstrap is the only module which
# can be loaded with default Python-machinery
# because the resulting extension is called `bootstrap`:
from . import bootstrap

# injecting our finders into sys.meta_path
# after that all other submodules can be loaded
bootstrap.bootstrap_cython_submodules()

from cython_extensions.combat_utils import (
    cy_attack_ready,
    cy_get_turn_speed,
    cy_is_facing,
    cy_pick_enemy_target,
    cy_range_vs_target,
)
from cython_extensions.general_utils import cy_pylon_matrix_covers, cy_unit_pending
from cython_extensions.geometry import (
    cy_angle_diff,
    cy_angle_to,
    cy_distance_to,
    cy_distance_to_squared,
    cy_find_average_angle,
    cy_find_correct_line,
    cy_get_angle_between_points,
    cy_towards,
    cy_translate_point_along_line,
)
from cython_extensions.map_analysis import cy_flood_fill_grid, cy_get_bounding_box
from cython_extensions.numpy_helper import (
    cy_all_points_below_max_value,
    cy_all_points_have_value,
    cy_last_index_with_value,
    cy_point_below_value,
    cy_points_with_value,
)
from cython_extensions.placement_solver import (
    can_place_structure,
    find_building_locations,
)
from cython_extensions.units_utils import (
    cy_center,
    cy_closest_to,
    cy_distance_to_squared,
    cy_in_attack_range,
    cy_sorted_by_distance_to,
)
