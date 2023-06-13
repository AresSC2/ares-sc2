from typing import TYPE_CHECKING

from sc2.ids.unit_typeid import UnitTypeId as UnitID

if TYPE_CHECKING:
    from ares import AresBot

def cy_unit_pending(ai: "AresBot", unit_type: UnitID) -> int:
    """Check how many unit_type are pending.

    Faster unit specific alternative to `python-sc2`'s `already_pending`

    453 ns ± 9.35 ns per loop (mean ± std. dev. of 7 runs, 1,000,000 loops each)

    Python-sc2 `already_pending` alternative:
    2.82 µs ± 29 ns per loop (mean ± std. dev. of 7 runs, 100,000 loops each)

    Parameters
    ----------
    ai :
        Bot object that will be running the game.
    unit_type :
        Unit type we want to check.

    Returns
    -------
    int :
        How many unit_type are currently building.

    """
    ...
