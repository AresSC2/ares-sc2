from typing import List

from .sc2_helper import circles_intersect as r_circles_intersect
from .sc2_helper import find_points_inside_circle as r_find_points_inside_circle


def circles_intersect(
    circle1_point2, circle2_point2, circle1_radius, circle2_radius
) -> bool:
    return r_circles_intersect(
        (circle1_point2[0], circle1_point2[1]),
        (circle2_point2[0], circle2_point2[1]),
        circle1_radius,
        circle2_radius,
    )


def find_points_inside_circle(
    point, radius: float, map_height: int, map_width: int
) -> List[(int, int)]:
    return r_find_points_inside_circle(point, radius, map_height, map_width)
