"""Ranges of enemy detectors with a safety buffer.

This is considered a dictionary for enemy detectors due to the safety buffer. Friendly
detectors will not be in range if they use these values.

"""

from __future__ import annotations

from sc2.ids.effect_id import EffectId
from sc2.ids.unit_typeid import UnitTypeId

DETECTOR_RANGES: dict[EffectId | UnitTypeId, float] = {
    # technically it's their range + radius + 1 (for safety)
    # Protoss
    UnitTypeId.OBSERVER: 11 + 0.5 + 1,
    UnitTypeId.OBSERVERSIEGEMODE: 13.75 + 0.5 + 1,
    UnitTypeId.PHOTONCANNON: 11 + 1.125 + 1,
    # Terran
    UnitTypeId.RAVEN: 11 + 0.625 + 1,
    UnitTypeId.MISSILETURRET: 11 + 1.125 + 1,
    EffectId.SCANNERSWEEP: 13 + 0 + 1,
    # Zerg
    UnitTypeId.OVERSEER: 11 + 1 + 1,
    UnitTypeId.OVERSEERSIEGEMODE: 13.75 + 1 + 1,
    UnitTypeId.SPORECRAWLER: 11 + 0.875 + 1,
}
