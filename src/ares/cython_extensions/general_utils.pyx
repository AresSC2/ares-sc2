from sc2.dicts.unit_trained_from import UNIT_TRAINED_FROM
from sc2.game_info import Race
from sc2.ids.unit_typeid import UnitTypeId

from ares.dicts.does_not_use_larva import DOES_NOT_USE_LARVA


cpdef unsigned int cy_unit_pending(object bot, object unit_type):
    cdef:
        unsigned int num_pending = 0
        unsigned int len_units, x
        set trained_from = UNIT_TRAINED_FROM[unit_type]
        object units_collection, unit

    if bot.race == Race.Zerg and unit_type != UnitTypeId.QUEEN:
        if unit_type in DOES_NOT_USE_LARVA:
            units_collection = bot.own_units
            len_units = len(bot.own_units)
            trained_from = {UnitTypeId[f"{unit_type.name}COCOON"]}
            if unit_type == UnitTypeId.LURKERMP:
                trained_from = {UnitTypeId.LURKERMPEGG}
            elif unit_type == UnitTypeId.OVERSEER:
                trained_from = {UnitTypeId.OVERLORDCOCOON}

            for x in range(len_units):
                unit = units_collection[x]
                if unit.type_id in trained_from:
                    num_pending += 1
            return num_pending
        # unit will be pending in eggs
        else:
            units_collection = bot.eggs
            len_units = len(units_collection)
            for x in range(len_units):
                egg = units_collection[x]
                if egg.orders and egg.orders[0].ability.button_name.upper() == unit_type.name:
                    num_pending += 1
            return num_pending

    # all other units, check the structures they are built from
    else:
        units_collection = bot.structures
        len_units = len(units_collection)
        for x in range(len_units):
            structure = units_collection[x]
            if structure.orders and structure.orders[0].ability.button_name.upper() == unit_type.name:
                num_pending += 1
            if (
                structure.has_reactor
                and structure.orders
                and len(structure.orders) > 1
                and structure.orders[1].ability.button_name.upper() == unit_type.name
            ):
                num_pending += 1
        return num_pending
