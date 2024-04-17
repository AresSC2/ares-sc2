"""Ranges of enemy detectors with a safety buffer.

This is considered a dictionary for enemy detectors due to the safety buffer. Friendly
detectors will not be in range if they use these values.

"""
from typing import Dict, Union

from sc2.ids.effect_id import EffectId
from sc2.ids.unit_typeid import UnitTypeId as UnitID

DETECTOR_RANGES: Dict[Union[EffectId, UnitID], float] = {
    # technically it's their range + radius + 1 (for safety)
    # Protoss
    UnitID.OBSERVER: 11 + 0.5 + 1,
    UnitID.OBSERVERSIEGEMODE: 13.75 + 0.5 + 1,
    UnitID.PHOTONCANNON: 11 + 1.125 + 1,
    # Terran
    UnitID.RAVEN: 11 + 0.625 + 1,
    UnitID.MISSILETURRET: 11 + 1.125 + 1,
    EffectId.SCANNERSWEEP: 13 + 0 + 1,
    # Zerg
    UnitID.OVERSEER: 11 + 1 + 1,
    UnitID.OVERSEERSIEGEMODE: 13.75 + 1 + 1,
    UnitID.SPORECRAWLER: 11 + 0.875 + 1,
}
