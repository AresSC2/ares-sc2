"""Range of enemy static defense that can target ground units.

Includes some offset, plus opinions on Planetary Fortresses.

"""
from typing import Dict

from sc2.ids.unit_typeid import UnitTypeId as UnitID

# value is the range plus some offset
ENEMY_VS_GROUND_STATIC_DEFENSE_TYPES: Dict[UnitID, int] = {
    # Protoss
    UnitID.PHOTONCANNON: 7 + 1,
    # Terran
    UnitID.BUNKER: 7 + 1,
    UnitID.PLANETARYFORTRESS: 12
    + 1
    + 2,  # much larger range than it has, but don't try to go behind them
    # Zerg
    UnitID.SPINECRAWLER: 7 + 1,
    UnitID.SPINECRAWLERUPROOTED: 7 + 1,
}
