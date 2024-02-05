from libc.math cimport atan2, fabs, pi

from cython_extensions.geometry import cy_angle_diff, cy_angle_to, cy_distance_to
from cython_extensions.turn_rate import TURN_RATE
from cython_extensions.unit_data import UNIT_DATA

UNIT_DATA_INT_KEYS = {k.value: v for k, v in UNIT_DATA.items()}
TURN_RATE_INT_KEYS = {k.value: v for k, v in TURN_RATE.items()}

cpdef double cy_get_turn_speed(unit, unsigned int unit_type_int):
    """Returns turn speed of unit in radians"""
    cdef double turn_rate

    turn_rate = TURN_RATE_INT_KEYS.get(unit_type_int, None)
    if turn_rate:
        return turn_rate * 1.4 * pi / 180

cpdef double cy_range_vs_target(unit, target):
    """Get the range of a unit to a target."""
    if unit.can_attack_air and target.is_flying:
        return unit.air_range
    else:
        return unit.ground_range

"""
End of `cdef` functions
"""

cpdef bint cy_is_facing(unit, other_unit, double angle_error=0.3):
    cdef:
        (double, double) p1 = unit.position
        (double, double) p2 = other_unit.position
        double angle, angle_difference
        double unit_facing = unit.facing

    angle = atan2(
        p2[1] - p1[1],
        p2[0] - p1[0],
    )
    if angle < 0:
        angle += pi * 2
    angle_difference = fabs(angle - unit_facing)
    return angle_difference < angle_error

cpdef bint cy_attack_ready(bot, unit, target):
    """
    Determine whether the unit can attack the target by the time the unit faces the target.
    Thanks Sasha for writing this out.
    """
    cdef:
        unsigned int unit_type_int = unit._proto.unit_type
        int weapon_cooldown
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
    angle = cy_angle_diff(
        unit.facing, cy_angle_to(unit_pos, target_pos)
    )
    turn_time = angle / cy_get_turn_speed(unit, unit_type_int)

    # Time it will take for unit to move in range of target
    distance = (
        cy_distance_to(unit_pos, target_pos)
        - unit.radius
        - target.radius
        - cy_range_vs_target(unit, target)
    )
    distance = max(0, distance)
    unit_speed = (unit.real_speed + 1e-16) * 1.4
    move_time = distance / unit_speed

    return step_time + turn_time + move_time >= weapon_cooldown / 22.4

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

    return returned_unit
