"""Ability base cooldowns.

"""
from typing import Dict

from sc2.ids.ability_id import AbilityId

# in frames
ABILITY_FRAME_COOL_DOWN: Dict = {
    # Protoss
    AbilityId.ADEPTPHASESHIFT_ADEPTPHASESHIFT: int(22.4 * 11) + 6,
    AbilityId.BEHAVIOR_PULSARBEAMON: int(22.4 * 4) + 6,
    AbilityId.EFFECT_BLINK_STALKER: int(22.4 * 7) + 6,
    AbilityId.EFFECT_PURIFICATIONNOVA: int(22.4 * 21.4) + 6,
    AbilityId.EFFECT_SHADOWSTRIDE: int(22.4 * 14) + 6,
    AbilityId.EFFECT_VOIDRAYPRISMATICALIGNMENT: int(22.4 * 42.9) + 6,
    AbilityId.ORACLEREVELATION_ORACLEREVELATION: int(22.4 * 10) + 6,
    # Terran
    AbilityId.EFFECT_MEDIVACIGNITEAFTERBURNERS: int(22.4 * 14) + 6,
    AbilityId.EFFECT_TACTICALJUMP: int(22.4 * 71) + 6,
    AbilityId.LOCKON_LOCKON: int(22.4 * 4.3) + 6,
    AbilityId.KD8CHARGE_KD8CHARGE: int(22.4 * 14) + 6,
    AbilityId.TACNUKESTRIKE_NUKECALLDOWN: int(22.4 * 14) + 6,
    AbilityId.WIDOWMINEATTACK_WIDOWMINEATTACK: int(22.4 * 29) + 6,
    AbilityId.YAMATO_YAMATOGUN: int(22.4 * 71) + 6,
    # Zerg
    AbilityId.CAUSTICSPRAY_CAUSTICSPRAY: int(22.4 * 32.14) + 6,
    AbilityId.EFFECT_CORROSIVEBILE: int(22.4 * 7.0) + 6,
    AbilityId.EFFECT_SPAWNLOCUSTS: int(22.4 * 43.0) + 8,
}
