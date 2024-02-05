from cython cimport boundscheck, wraparound

from math import floor

from sc2.dicts.unit_trained_from import UNIT_TRAINED_FROM
from sc2.game_info import Race
from sc2.ids.unit_typeid import UnitTypeId

from cython_extensions.geometry import cy_distance_to_squared

DOES_NOT_USE_LARVA: dict[UnitTypeId, UnitTypeId] = {
    UnitTypeId.BANELING: UnitTypeId.ZERGLING,
    UnitTypeId.BROODLORD: UnitTypeId.CORRUPTOR,
    UnitTypeId.LURKERMP: UnitTypeId.HYDRALISK,
    UnitTypeId.OVERSEER: UnitTypeId.OVERLORD,
    UnitTypeId.OVERLORDTRANSPORT: UnitTypeId.OVERLORD,
    UnitTypeId.RAVAGER: UnitTypeId.ROACH,
}

@boundscheck(False)
@wraparound(False)
cpdef bint cy_pylon_matrix_covers(
        (double, double) position,
        object pylons,
        const unsigned char[:, :] height_grid,
        double pylon_build_progress = 1.0
    ):

    cdef:
        unsigned int x = int(position[0])
        unsigned int y = int(position[1])
        Py_ssize_t len_pylons = len(pylons)
        unsigned int position_height = height_grid[y, x]
        (double, double) pylon_position
        unsigned int pylon_height, i, _x, _y
        # range + pylon radius
        # squared distance
        double pylon_powered_distance = 42.25 #  + 1.125


    for i in range(len_pylons):
        pylon = pylons[i]
        pylon_position = pylon.position
        _x = int(pylon_position[0])
        _y = int(pylon_position[1])
        pylon_height = height_grid[_y, _x]
        if (
          pylon.build_progress >= pylon_build_progress
          and pylon_height >= position_height
          and cy_distance_to_squared(position, pylon_position) < pylon_powered_distance
        ):
          return True

    return False

cpdef unsigned int cy_unit_pending(object bot, object unit_type):
    cdef:
        unsigned int num_pending = 0
        Py_ssize_t len_units, x
        object units_collection, unit

    trained_from = UNIT_TRAINED_FROM[unit_type]

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
