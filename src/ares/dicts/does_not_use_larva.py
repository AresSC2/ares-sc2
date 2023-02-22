"""Zerg units that do not use Larva.

"""
from typing import Dict

from sc2.ids.unit_typeid import UnitTypeId as UnitID

# key is the unit to build, value is the unit it builds from
DOES_NOT_USE_LARVA: Dict[UnitID, UnitID] = {
    UnitID.BANELING: UnitID.ZERGLING,
    UnitID.BROODLORD: UnitID.CORRUPTOR,
    UnitID.LURKERMP: UnitID.HYDRALISK,
    UnitID.OVERSEER: UnitID.OVERLORD,
    UnitID.OVERLORDTRANSPORT: UnitID.OVERLORD,
    UnitID.RAVAGER: UnitID.ROACH,
}
