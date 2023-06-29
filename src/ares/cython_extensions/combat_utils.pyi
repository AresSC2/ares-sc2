from typing import Union

import numpy as np
from sc2.unit import Unit
from sc2.units import Units

from ares import AresBot

def cy_attack_ready(ai: AresBot, unit: Unit, target: Unit) -> bool:
    """Check if the unit is ready to attack the target.

    1.46 µs ± 5.45 ns per loop (mean ± std. dev. of 7 runs, 1,000,000 loops each)

    Python alternative:
    5.66 µs ± 21.2 ns per loop (mean ± std. dev. of 7 runs, 100,000 loops each)

    Parameters
    ----------
    ai :
        Bot object that will be running the game.
    unit :
        The unit we want to check.
    target :
        The thing we want to shoot.

    Returns
    -------
    bool :
        Is the unit ready to attack the target?

    """
    ...

def cy_is_facing(unit: Unit, other_unit: Unit, angle_error: float = 0.05) -> bool:
    """Given a grid of influence, check if the given position is above weight_safety_limit.

    323 ns ± 3.93 ns per loop (mean ± std. dev. of 7 runs, 1,000,000 loops each)

    Python-sc2's `unit.is_facing(other_unit)` alternative:
    2.94 µs ± 8 ns per loop (mean ± std. dev. of 7 runs, 100,000 loops each)

    Parameters
    ----------
    unit :
        2D grid to check with influence.
    other_unit :
        Position converted to x/y integers.
    angle_error :
        At what threshold is this position deemed unsafe.

    Returns
    -------
    bool :
        True if unit is facing other_unit.

    """
    ...

def cy_is_position_safe(
    grid: np.ndarray, position: tuple[int, int], weight_safety_limit: float
) -> bool:
    """Given a grid of influence, check if the given position is above weight_safety_limit.

    627 ns ± 3.12 ns per loop (mean ± std. dev. of 7 runs, 1,000,000 loops each)

    Python alternative:
    4.02 µs ± 20.4 ns per loop (mean ± std. dev. of 7 runs, 100,000 loops each)

    Parameters
    ----------
    grid :
        2D grid to check with influence.
    position :
        Position converted to x/y integers.
    weight_safety_limit :
        At what threshold is this position deemed unsafe.

    Returns
    -------
    bool :
        This position is safe accoring to weight_safety_limit

    """
    ...

def cy_pick_enemy_target(enemies: Union[Units, list[Unit]]) -> Unit:
    """Pick the best thing to shoot at out of all enemies.

    TODO: If there are multiple units that can be killed, pick the highest value one
        Unit parameter to allow for this in the future.
    TODO: There might be other things to consider here.

    70.5 µs ± 818 ns per loop (mean ± std. dev. of 7 runs, 10,000 loops each)

    Python alternative:
    115 µs ± 766 ns per loop (mean ± std. dev. of 7 runs, 10,000 loops each)

    Parameters
    ----------
    enemies :
        All enemy units we would like to check.

    Returns
    -------
    Unit :
        The best unit to target.
    """
    ...
