from sc2.ids.unit_typeid import UnitTypeId as UnitID

from ares.consts import BuildingSize

# Note, no terran flying structures as we only care about placements here
# only working on 2x2 and 3x3 for now
STRUCTURE_TO_BUILDING_SIZE: dict[UnitID, BuildingSize] = {
    # protoss 2x2
    UnitID.PHOTONCANNON: BuildingSize.TWO_BY_TWO,
    UnitID.PYLON: BuildingSize.TWO_BY_TWO,
    UnitID.SHIELDBATTERY: BuildingSize.TWO_BY_TWO,
    # protoss 3x3
    UnitID.CYBERNETICSCORE: BuildingSize.THREE_BY_THREE,
    UnitID.FLEETBEACON: BuildingSize.THREE_BY_THREE,
    UnitID.FORGE: BuildingSize.THREE_BY_THREE,
    UnitID.GATEWAY: BuildingSize.THREE_BY_THREE,
    UnitID.ROBOTICSBAY: BuildingSize.THREE_BY_THREE,
    UnitID.ROBOTICSFACILITY: BuildingSize.THREE_BY_THREE,
    UnitID.STARGATE: BuildingSize.THREE_BY_THREE,
    UnitID.TEMPLARARCHIVE: BuildingSize.THREE_BY_THREE,
    UnitID.TWILIGHTCOUNCIL: BuildingSize.THREE_BY_THREE,
    # protoss 5x5
    UnitID.NEXUS: BuildingSize.FIVE_BY_FIVE,
    # terran 2x2
    UnitID.MISSILETURRET: BuildingSize.TWO_BY_TWO,
    UnitID.SENSORTOWER: BuildingSize.TWO_BY_TWO,
    UnitID.SUPPLYDEPOT: BuildingSize.TWO_BY_TWO,
    # terran 3x3
    UnitID.ARMORY: BuildingSize.THREE_BY_THREE,
    UnitID.BARRACKS: BuildingSize.THREE_BY_THREE,
    UnitID.BUNKER: BuildingSize.THREE_BY_THREE,
    UnitID.ENGINEERINGBAY: BuildingSize.THREE_BY_THREE,
    UnitID.FACTORY: BuildingSize.THREE_BY_THREE,
    UnitID.FUSIONCORE: BuildingSize.THREE_BY_THREE,
    UnitID.GHOSTACADEMY: BuildingSize.THREE_BY_THREE,
    UnitID.STARPORT: BuildingSize.THREE_BY_THREE,
    # terran 5x5
    UnitID.COMMANDCENTER: BuildingSize.FIVE_BY_FIVE,
    # zerg 2x2
    UnitID.SPINECRAWLER: BuildingSize.TWO_BY_TWO,
    UnitID.SPIRE: BuildingSize.TWO_BY_TWO,
    UnitID.SPORECRAWLER: BuildingSize.TWO_BY_TWO,
    # zerg 3x3
    UnitID.BANELINGNEST: BuildingSize.THREE_BY_THREE,
    UnitID.EVOLUTIONCHAMBER: BuildingSize.THREE_BY_THREE,
    UnitID.HYDRALISKDEN: BuildingSize.THREE_BY_THREE,
    UnitID.INFESTATIONPIT: BuildingSize.THREE_BY_THREE,
    UnitID.LURKERDENMP: BuildingSize.THREE_BY_THREE,
    UnitID.NYDUSCANAL: BuildingSize.THREE_BY_THREE,
    UnitID.NYDUSNETWORK: BuildingSize.THREE_BY_THREE,
    UnitID.ROACHWARREN: BuildingSize.THREE_BY_THREE,
    UnitID.SPAWNINGPOOL: BuildingSize.THREE_BY_THREE,
    UnitID.ULTRALISKCAVERN: BuildingSize.THREE_BY_THREE,
    # zerg 5x5
    UnitID.HATCHERY: BuildingSize.FIVE_BY_FIVE,
}
