import numpy as np

cimport numpy as cnp
from cython cimport boundscheck, wraparound
from libc.math cimport atan2, fabs, pi

from ares.cython_extensions.geometry import cy_distance_to
from ares.dicts.turn_rate import TURN_RATE
from ares.dicts.unit_data import UNIT_DATA

UNIT_DATA_INT_KEYS = {k.value: v for k, v in UNIT_DATA.items()}
TURN_RATE_INT_KEYS = {k.value: v for k, v in TURN_RATE.items()}

# `cdef` functions only for internal use, change to `cpdef` if
# needed elsewhere
cdef double angle_to((float, float) from_pos, (float, float) to_pos):
    """Angle from point to other point in radians"""
    return atan2(to_pos[1] - from_pos[1], to_pos[0] - to_pos[0])

cdef double angle_diff(double a, double b):
    """Absolute angle difference between 2 angles"""
    if a < 0:
        a += pi * 2
    if b < 0:
        b += pi * 2
    return fabs(a - b)

cdef double get_turn_speed(unit, unsigned int unit_type_int):
    """Returns turn speed of unit in radians"""
    cdef double turn_rate

    turn_rate = TURN_RATE_INT_KEYS.get(unit_type_int, None)
    if turn_rate:
        return turn_rate * 1.4 * pi / 180

cdef double range_vs_target(unit, target):
    """Get the range of a unit to a target."""
    if unit.can_attack_air and target.is_flying:
        return unit.air_range
    else:
        return unit.ground_range

"""
End of `cdef` functions
"""

cpdef bint cy_attack_ready(bot, unit, target):
    """
    Determine whether the unit can attack the target by the time the unit faces the target.
    Thanks Sasha for writing this out.
    """
    cdef:
        unsigned int unit_type_int = unit._proto.unit_type
        unsigned int weapon_cooldown
        double angle, distance, move_time, step_time, turn_time, unit_speed
        (float, float) unit_pos
        (float, float) target_pos

    # fix for units, where this method returns False so the unit moves
    # but the attack animation is still active, so the move command cancels the attack
    # need to think of a better fix later, but this is better than a unit not attacking
    # and still better than using simple weapon.cooldown == 0 micro
    weapon_cooldown = unit.weapon_cooldown
    # if weapon_cooldown > 7: # and unit_type_int == 91:  # 91 == UnitID.HYDRALISK
    #     return True
    # prevents crash, since unit can't move
    if unit_type_int == 503:  # 503 == UnitID.LURKERMPBURROWED
        return True
    if not unit.can_attack:
        return False
    # Time elapsed per game step
    step_time = bot.client.game_step / 22.4

    unit_pos = unit.position
    target_pos = target.position
    # Time it will take for unit to turn to face target
    angle = angle_diff(
        unit.facing, angle_to(unit_pos, target_pos)
    )
    turn_time = angle / get_turn_speed(unit, unit_type_int)

    # Time it will take for unit to move in range of target
    distance = (
        cy_distance_to(unit_pos, target_pos)
        - unit.radius
        - target.radius
        - range_vs_target(unit, target)
    )
    distance = max(0, distance)
    unit_speed = (unit.real_speed + 1e-16) * 1.4
    move_time = distance / unit_speed

    return step_time + turn_time + move_time >= weapon_cooldown / 22.4

@boundscheck(False)
@wraparound(False)
cpdef bint cy_is_position_safe(
    cnp.ndarray[cnp.npy_float32, ndim=2] grid,
    (unsigned int, unsigned int) position,
    double weight_safety_limit = 1.0,
):
    """
    987 ns ± 10.1 ns per loop (mean ± std. dev. of 7 runs, 1,000,000 loops each)
    Python alternative:
    4.66 µs ± 64.8 ns per loop (mean ± std. dev. of 7 runs, 100,000 loops each)
    """
    cdef double weight = 0.0
    weight = grid[position[0], position[1]]
    # np.inf check if drone is pathing near a spore crawler
    return weight == np.inf or weight <= weight_safety_limit

cpdef object cy_pick_enemy_target(object enemies):
    """For best enemy target from the provided enemies
    TODO: If there are multiple units that can be killed, pick the highest value one
        Unit parameter to allow for this in the future

    For now this returns the lowest health enemy
    """
    cdef:
        object returned_unit
        unsigned int num_enemies, x
        double lowest_health, total_health

    num_enemies = len(enemies)
    returned_unit = enemies[0]
    lowest_health = 999.9
    for x in range(num_enemies):
        unit = enemies[x]
        total_health = unit.health + unit.shield
        if total_health < lowest_health:
            lowest_health = total_health
            returned_unit = unit

    return unit
