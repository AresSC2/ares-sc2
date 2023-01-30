"""Weights for influence mapping.

These are units that have been given custom values. Not all units are here, since
values are taken from the API for some units.

"""

from typing import Dict

from sc2.ids.unit_typeid import UnitTypeId as UnitID

# Zerg building data includes Drone cost
WEIGHT_COSTS: Dict[UnitID, Dict] = {
    UnitID.ADEPT: {"AirCost": 0, "GroundCost": 9, "AirRange": 0, "GroundRange": 5},
    UnitID.ADEPTPHASESHIFT: {
        "AirCost": 0,
        "GroundCost": 9,
        "AirRange": 0,
        "GroundRange": 5,
    },
    UnitID.AUTOTURRET: {
        "AirCost": 31,
        "GroundCost": 31,
        "AirRange": 7,
        "GroundRange": 7,
    },
    UnitID.ARCHON: {"AirCost": 40, "GroundCost": 40, "AirRange": 3, "GroundRange": 3},
    UnitID.BANELING: {"AirCost": 0, "GroundCost": 20, "AirRange": 0, "GroundRange": 3},
    UnitID.BANSHEE: {"AirCost": 0, "GroundCost": 12, "AirRange": 0, "GroundRange": 6},
    UnitID.BATTLECRUISER: {
        "AirCost": 31,
        "GroundCost": 50,
        "AirRange": 6,
        "GroundRange": 6,
    },
    UnitID.CARRIER: {
        "AirCost": 20,
        "GroundCost": 20,
        "AirRange": 11,
        "GroundRange": 11,
    },
    UnitID.CORRUPTOR: {"AirCost": 10, "GroundCost": 0, "AirRange": 6, "GroundRange": 0},
    UnitID.CYCLONE: {"AirCost": 27, "GroundCost": 27, "AirRange": 7, "GroundRange": 7},
    UnitID.GHOST: {"AirCost": 10, "GroundCost": 10, "AirRange": 6, "GroundRange": 6},
    UnitID.HELLION: {"AirCost": 0, "GroundCost": 8, "AirRange": 0, "GroundRange": 8},
    UnitID.HYDRALISK: {
        "AirCost": 20,
        "GroundCost": 20,
        "AirRange": 6,
        "GroundRange": 6,
    },
    UnitID.INFESTOR: {
        "AirCost": 30,
        "GroundCost": 30,
        "AirRange": 10,
        "GroundRange": 10,
    },
    UnitID.LIBERATOR: {"AirCost": 10, "GroundCost": 0, "AirRange": 5, "GroundRange": 0},
    UnitID.MARINE: {"AirCost": 10, "GroundCost": 10, "AirRange": 5, "GroundRange": 5},
    UnitID.MOTHERSHIP: {
        "AirCost": 23,
        "GroundCost": 23,
        "AirRange": 7,
        "GroundRange": 7,
    },
    UnitID.MUTALISK: {"AirCost": 8, "GroundCost": 8, "AirRange": 3, "GroundRange": 3},
    UnitID.ORACLE: {"AirCost": 0, "GroundCost": 24, "AirRange": 0, "GroundRange": 4},
    UnitID.PHOENIX: {"AirCost": 15, "GroundCost": 0, "AirRange": 7, "GroundRange": 0},
    UnitID.QUEEN: {
        "AirCost": 12.6,
        "GroundCost": 11.2,
        "AirRange": 7,
        "GroundRange": 5,
    },
    UnitID.SENTRY: {"AirCost": 8.4, "GroundCost": 8.4, "AirRange": 5, "GroundRange": 5},
    UnitID.STALKER: {"AirCost": 10, "GroundCost": 10, "AirRange": 6, "GroundRange": 6},
    UnitID.TEMPEST: {
        "AirCost": 17,
        "GroundCost": 17,
        "AirRange": 14,
        "GroundRange": 10,
    },
    UnitID.THOR: {"AirCost": 28, "GroundCost": 28, "AirRange": 11, "GroundRange": 7},
    UnitID.VIKINGASSAULT: {
        "AirCost": 0,
        "GroundCost": 17,
        "AirRange": 0,
        "GroundRange": 6,
    },
    UnitID.VIKINGFIGHTER: {
        "AirCost": 14,
        "GroundCost": 0,
        "AirRange": 9,
        "GroundRange": 0,
    },
    UnitID.VOIDRAY: {"AirCost": 20, "GroundCost": 20, "AirRange": 6, "GroundRange": 6},
    UnitID.WIDOWMINEBURROWED: {
        "AirCost": 150,
        "GroundCost": 150,
        "AirRange": 5.5,
        "GroundRange": 5.5,
    },
}
