"""Range of enemy static defense that can target ground units.

Includes some offset, plus opinions on Planetary Fortresses.

"""

from sc2.ids.unit_typeid import UnitTypeId

# value is the range plus some offset
ENEMY_VS_GROUND_STATIC_DEFENSE_TYPES: dict[UnitTypeId, int] = {
    # Protoss
    UnitTypeId.PHOTONCANNON: 7 + 1,
    # Terran
    UnitTypeId.BUNKER: 7 + 1,
    UnitTypeId.PLANETARYFORTRESS: 12
    + 1
    + 2,  # much larger range than it has, but don't try to go behind them
    # Zerg
    UnitTypeId.SPINECRAWLER: 7 + 1,
    UnitTypeId.SPINECRAWLERUPROOTED: 7 + 1,
}
