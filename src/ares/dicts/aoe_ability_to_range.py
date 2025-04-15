from sc2.ids.ability_id import AbilityId
from sc2.ids.buff_id import BuffId
from sc2.ids.effect_id import EffectId

AOE_ABILITY_SPELLS_INFO: dict[AbilityId, dict] = {
    AbilityId.BLINDINGCLOUD_BLINDINGCLOUD: {
        "radius": 2.0,
        "range": 10.0,
        "effect": EffectId.BLINDINGCLOUDCP,
    },
    AbilityId.EFFECT_CORROSIVEBILE: {
        "radius": 0.5,
        "range": 9.0,
        "effect": EffectId.RAVAGERCORROSIVEBILECP,
    },
    AbilityId.EFFECT_ANTIARMORMISSILE: {
        "radius": 2.88,
        "range": 10.0,
        "effect": BuffId.RAVENSHREDDERMISSILEARMORREDUCTION,
    },
    AbilityId.EMP_EMP: {"radius": 1.5, "range": 10.0, "effect": None},
    AbilityId.FUNGALGROWTH_FUNGALGROWTH: {
        "radius": 2.25,
        "range": 10.0,
        "effect": BuffId.FUNGALGROWTH,
    },
    AbilityId.KD8CHARGE_KD8CHARGE: {"radius": 5.0, "range": 2.0, "effect": None},
    AbilityId.PARASITICBOMB_PARASITICBOMB: {
        "radius": 3.0,
        "range": 8.0,
        "effect": BuffId.PARASITICBOMB,
    },
    AbilityId.PSISTORM_PSISTORM: {
        "radius": 1.5,
        "range": 9.0,
        "effect": EffectId.PSISTORMPERSISTENT,
    },
    AbilityId.TACNUKESTRIKE_NUKECALLDOWN: {
        "radius": 12.0,
        "range": 9.0,
        "effect": EffectId.NUKEPERSISTENT,
    },
}
