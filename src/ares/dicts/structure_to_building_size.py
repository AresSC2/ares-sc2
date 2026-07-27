from sc2.ids.unit_typeid import UnitTypeId

from ares.consts import BuildingSize

# Note, no terran flying structures as we only care about placements here
# only working on 2x2 and 3x3 for now
STRUCTURE_TO_BUILDING_SIZE: dict[UnitTypeId, BuildingSize] = {
    # protoss 2x2
    UnitTypeId.PHOTONCANNON: BuildingSize.TWO_BY_TWO,
    UnitTypeId.PYLON: BuildingSize.TWO_BY_TWO,
    UnitTypeId.SHIELDBATTERY: BuildingSize.TWO_BY_TWO,
    UnitTypeId.DARKSHRINE: BuildingSize.TWO_BY_TWO,
    # protoss 3x3
    UnitTypeId.CYBERNETICSCORE: BuildingSize.THREE_BY_THREE,
    UnitTypeId.FLEETBEACON: BuildingSize.THREE_BY_THREE,
    UnitTypeId.FORGE: BuildingSize.THREE_BY_THREE,
    UnitTypeId.GATEWAY: BuildingSize.THREE_BY_THREE,
    UnitTypeId.ROBOTICSBAY: BuildingSize.THREE_BY_THREE,
    UnitTypeId.ROBOTICSFACILITY: BuildingSize.THREE_BY_THREE,
    UnitTypeId.STARGATE: BuildingSize.THREE_BY_THREE,
    UnitTypeId.TEMPLARARCHIVE: BuildingSize.THREE_BY_THREE,
    UnitTypeId.TWILIGHTCOUNCIL: BuildingSize.THREE_BY_THREE,
    # protoss 5x5
    UnitTypeId.NEXUS: BuildingSize.FIVE_BY_FIVE,
    # terran 2x2
    UnitTypeId.MISSILETURRET: BuildingSize.TWO_BY_TWO,
    UnitTypeId.SENSORTOWER: BuildingSize.TWO_BY_TWO,
    UnitTypeId.SUPPLYDEPOT: BuildingSize.TWO_BY_TWO,
    # terran 3x3
    UnitTypeId.ARMORY: BuildingSize.THREE_BY_THREE,
    UnitTypeId.BARRACKS: BuildingSize.THREE_BY_THREE,
    UnitTypeId.BUNKER: BuildingSize.THREE_BY_THREE,
    UnitTypeId.ENGINEERINGBAY: BuildingSize.THREE_BY_THREE,
    UnitTypeId.FACTORY: BuildingSize.THREE_BY_THREE,
    UnitTypeId.FUSIONCORE: BuildingSize.THREE_BY_THREE,
    UnitTypeId.GHOSTACADEMY: BuildingSize.THREE_BY_THREE,
    UnitTypeId.STARPORT: BuildingSize.THREE_BY_THREE,
    # terran 5x5
    UnitTypeId.COMMANDCENTER: BuildingSize.FIVE_BY_FIVE,
    # zerg 2x2
    UnitTypeId.SPINECRAWLER: BuildingSize.TWO_BY_TWO,
    UnitTypeId.SPIRE: BuildingSize.TWO_BY_TWO,
    UnitTypeId.SPORECRAWLER: BuildingSize.TWO_BY_TWO,
    # zerg 3x3
    UnitTypeId.BANELINGNEST: BuildingSize.THREE_BY_THREE,
    UnitTypeId.EVOLUTIONCHAMBER: BuildingSize.THREE_BY_THREE,
    UnitTypeId.HYDRALISKDEN: BuildingSize.THREE_BY_THREE,
    UnitTypeId.INFESTATIONPIT: BuildingSize.THREE_BY_THREE,
    UnitTypeId.LURKERDENMP: BuildingSize.THREE_BY_THREE,
    UnitTypeId.NYDUSCANAL: BuildingSize.THREE_BY_THREE,
    UnitTypeId.NYDUSNETWORK: BuildingSize.THREE_BY_THREE,
    UnitTypeId.ROACHWARREN: BuildingSize.THREE_BY_THREE,
    UnitTypeId.SPAWNINGPOOL: BuildingSize.THREE_BY_THREE,
    UnitTypeId.ULTRALISKCAVERN: BuildingSize.THREE_BY_THREE,
    # zerg 5x5
    UnitTypeId.HATCHERY: BuildingSize.FIVE_BY_FIVE,
}
