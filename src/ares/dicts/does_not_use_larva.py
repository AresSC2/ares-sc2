"""Zerg units that do not use Larva."""

from sc2.ids.unit_typeid import UnitTypeId

# key is the unit to build, value is the unit it builds from
DOES_NOT_USE_LARVA: dict[UnitTypeId, UnitTypeId] = {
    UnitTypeId.BANELING: UnitTypeId.ZERGLING,
    UnitTypeId.BROODLORD: UnitTypeId.CORRUPTOR,
    UnitTypeId.LURKERMP: UnitTypeId.HYDRALISK,
    UnitTypeId.OVERSEER: UnitTypeId.OVERLORD,
    UnitTypeId.OVERLORDTRANSPORT: UnitTypeId.OVERLORD,
    UnitTypeId.RAVAGER: UnitTypeId.ROACH,
}
