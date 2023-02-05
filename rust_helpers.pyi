from typing import Dict, List, Set, Tuple, Union
import numpy as np
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units

def adjust_combat_formation(
        our_units: Units,
        enemies: Units,
        fodder_tags: List[int],
        core_unit_multiplier: float,
        fodder_unit_multiplier: float,
        retreat_angle: float
) -> Dict[int, Tuple[float, float]]: ...

def adjust_moving_formation(
        our_units: Units,
        target: Tuple[float, float],
        fodder_tags: List[int],
        core_unit_multiplier: float,
        retreat_angle: float
) -> Dict[int, Tuple[float, float]]: ...

def all_points_have_creep(
        points: List[Tuple[int, int]],
        creep: np.ndarray,
) -> bool: ...

def closest_unit_index_to(
        units: Units,
        target_position: Union[Point2, Tuple[float, float]]
)-> int: ...

def closest_position_index_to(
        positions: List[Union[Point2, Tuple[float, float]]],
        target_position: Union[Point2, Tuple[float, float]]
)-> int: ...

def cdist(
        xa: List[Union[List[float], Tuple[float, float]]],
        xb: List[Union[List[float], Tuple[float, float]]],
) -> List[List[float]]: ...

def find_center_mass(
        units: Units,
        distance: float,
        default_position: Union[List[float], Point2]
) -> Tuple[int, List[float]]: ...

def find_ling_drop_point(
        terrain_map: np.ndarray,
        pathing_map: np.ndarray,
        rounded_enemy_start: Tuple[int, int],
        away_from_point: Tuple[float, float],
        base_perimeter_points: List[Tuple[int, int]],
        search_area: int,
) -> Tuple[int, int]: ...

def get_blocked_spore_position(
        unit: Unit,
        distances: np.ndarray,
        creep: np.ndarray,
        placement: np.ndarray,
        vision: np.ndarray,
        units_to_avoid:Units,
) -> Tuple[int, int]: ...

def get_positions_closer_than(
        search_positions: List[Tuple[float, float]],
        start_position: Tuple[float, float],
        distance: float
) -> List[Tuple[float, float]]: ...

def get_spore_forest_positions(
        rows_columns: Tuple[int, int],
        center_point: Union[Point2, Tuple[float, float]],
        spacing: float,
        creep: np.ndarray,
        placement: np.ndarray,
        vision: np.ndarray,
        units_to_avoid: Units
) -> Tuple[List[Tuple[int, int], List[Tuple[int, int]]]]: ...

def get_usize_positions_closer_than(
        search_positions: List[Tuple[int, int]],
        start_position: Tuple[float, float],
        distance: float
) -> List[Tuple[int, int]]: ...

def is_valid_2x2_position(
        raw_point: Tuple[int, int],
        units_to_avoid: Units,
        vision_grid: np.ndarray,
        placement_grid: np.ndarray,
        creep_grid: np.ndarray,
) -> bool: ...

def make_bounding_circle(
        points: List[List[float]]
) -> Tuple[float, float, float]: ...

def number_of_chokes_pathed_through(
        path: List[Tuple[int, int]],
        chokes_list: List[Set[Tuple[int, int]]],
) -> int: ...

def surround_complete(
        units: Units,
        our_center: Union[List[float], Point2],
        enemy_center: Union[List[float], Point2],
        offset: float,
        _ratio: float,
) -> bool: ...

def terrain_flood_fill(
        start_point: Tuple[int, int],
        terrain_grid: np.ndarray,
        pathing_grid: np.ndarray,
        max_distance: float,
        choke_points: Set[Tuple[int, int]],
) -> List[Tuple[int, int]]: ...
