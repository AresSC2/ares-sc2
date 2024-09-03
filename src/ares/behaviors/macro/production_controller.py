from dataclasses import dataclass
from typing import TYPE_CHECKING

from cython_extensions import cy_distance_to_squared
from loguru import logger
from sc2.data import Race
from sc2.dicts.unit_trained_from import UNIT_TRAINED_FROM
from sc2.dicts.unit_unit_alias import UNIT_UNIT_ALIAS
from sc2.ids.unit_typeid import UnitTypeId as UnitID
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units

from ares.consts import ADD_ONS, GATEWAY_UNITS, ID, TARGET, TECHLAB_TYPES
from ares.dicts.unit_tech_requirement import UNIT_TECH_REQUIREMENT

if TYPE_CHECKING:
    from ares import AresBot

from ares.behaviors.macro import BuildStructure, MacroBehavior
from ares.behaviors.macro.restore_power import RestorePower
from ares.managers.manager_mediator import ManagerMediator


@dataclass
class ProductionController(MacroBehavior):
    """Handle creating extra production facilities based
    on an army composition dictionary.
    This dictionary should be structured the same as the one
    passed into SpawnController

    Terran / Protoss only

    Example bot code:
    ```py
    from ares.behaviors.production_controller import ProductionController

    # Note: This does not try to build production facilities and
    # will ignore units that are impossible to currently spawn.
    army_composition: dict[UnitID: {float, bool}] = {
        UnitID.MARINE: {"proportion": 0.6, "priority": 2},  # lowest priority
        UnitID.MEDIVAC: {"proportion": 0.25, "priority": 1},
        UnitID.SIEGETANK: {"proportion": 0.15, "priority": 0},  # highest priority
    }
    # where `self` is an `AresBot` object
    self.register_behavior(ProductionController(
        army_composition, self.ai.start_location))

    ```

    Attributes
    ----------
    army_composition_dict : dict[UnitID: float, bool]
        A dictionary that details how an army composition should be made up.
        The proportional values should all add up to 1.0.
        With a priority integer to give units emphasis.
    base_location : Point2
        Where abouts do we build production?
    unit_pending_progress : float (default = 0.8)
        Check for production structures almost ready
        For example a marine might almost be ready, meaning
        we don't need to add extra production just yet.
    ignore_below_unit_count : int (default = 0)
        If there is little to no army, this behavior might
        make undesirable decisions.
    ignore_below_proportion: float = 0.05
        If we don't want many of this unit, no point adding production.
        Will check if possible to build unit first.
    should_repower_structures: bool = True
        Search for unpowered structures, and build a new
        pylon as needed.
    """

    army_composition_dict: dict[UnitID, dict[str, float, str, int]]
    base_location: Point2
    unit_pending_progress: float = 0.75
    ignore_below_unit_count: int = 0
    ignore_below_proportion: float = 0.05
    should_repower_structures: bool = True

    def execute(self, ai: "AresBot", config: dict, mediator: ManagerMediator) -> bool:
        assert (
            ai.race != Race.Zerg
        ), "ProductionController behavior is for Protoss and Terran only"
        if ai.race == Race.Protoss and self.should_repower_structures:
            if RestorePower().execute(ai, config, mediator):
                return True

        army_comp_dict: dict = self.army_composition_dict

        assert isinstance(
            army_comp_dict, dict
        ), f"self.army_composition_dict should be dict type, got {type(army_comp_dict)}"

        # get the current standing army based on the army comp dict
        # note we don't consider units outside the army comp dict
        unit_types: list[UnitID] = [*army_comp_dict]
        num_total_units: int = 0
        for unit_type in unit_types:
            num_total_units += mediator.get_own_unit_count(unit_type_id=unit_type)

        if num_total_units < self.ignore_below_unit_count:
            return False

        proportion_sum: float = 0.0
        structure_dict: dict[UnitID, Units] = mediator.get_own_structures_dict

        flying_structures: dict[int, dict] = mediator.get_flying_structure_tracker
        collection_rate: int = (
            ai.state.score.collection_rate_minerals
            + ai.state.score.collection_rate_vespene
        )

        # iterate through desired army comp starting with the highest priority unit
        for unit_type_id, army_comp_info in sorted(
            army_comp_dict.items(), key=lambda x: x[1].get("priority", int(0))
        ):
            assert isinstance(unit_type_id, UnitID), (
                f"army_composition_dict expects UnitTypeId type as keys, "
                f"got {type(unit_type_id)}"
            )
            target_proportion: float = army_comp_info["proportion"]
            proportion_sum += target_proportion
            num_this_unit: int = mediator.get_own_unit_count(unit_type_id=unit_type_id)
            current_proportion: float = num_this_unit / (num_total_units + 1e-16)

            # already have enough of this unit type, don't need production
            # add a bit of multiplier so not to overreact when near threshold
            if current_proportion * 1.1 >= target_proportion:
                continue

            # we don't want to add extra production for this unit
            # but ensure it's possible to build at some point
            if (
                target_proportion < self.ignore_below_proportion
                and ai.tech_ready_for_unit(unit_type_id)
            ):
                continue

            train_from: set[UnitID] = UNIT_TRAINED_FROM[unit_type_id]
            trained_from: UnitID = next(iter(UNIT_TRAINED_FROM[unit_type_id]))
            if unit_type_id in GATEWAY_UNITS:
                trained_from = UnitID.GATEWAY

            if self._not_started_but_in_building_tracker(ai, mediator, trained_from):
                continue

            # we need to tech up
            if self._teching_up(ai, unit_type_id, trained_from):
                return True

            # get all idle build structures/units we can create this unit from
            # if we can already build this unit, we don't need production.
            if (
                len(
                    ai.get_build_structures(
                        train_from,
                        unit_type_id,
                    )
                )
                > 0
            ):
                continue

            # are we low on resources? don't add production
            if not ai.can_afford(trained_from):
                continue

            if not ai.tech_ready_for_unit(unit_type_id):
                continue

            # if we have a production building floating, wait
            if ai.race == Race.Terran:
                prod_flying: bool = False
                # might have this structure flying
                for tag in flying_structures:
                    if unit := ai.unit_tag_dict.get(tag, None):
                        if unit.type_id in UNIT_UNIT_ALIAS:
                            for s_id in train_from:
                                if UNIT_UNIT_ALIAS[unit.type_id] == s_id:
                                    prod_flying = True
                                    break
                if prod_flying:
                    continue

            # income might not support more production
            existing_structures: list[Unit] = []
            for structure_type in train_from:
                existing_structures.extend(structure_dict[structure_type])
            # target proportion is low, don't add extra pending
            if target_proportion <= 0.15 and (
                any([ai.structure_pending(type_id) for type_id in train_from])
            ):
                continue

            divide_by: int = 420 if unit_type_id in GATEWAY_UNITS else 760
            if len(existing_structures) >= int(collection_rate / divide_by):
                continue

            # might have production almost ready
            almost_ready: bool = False
            for structure_type in train_from:
                if structure_type == UnitID.WARPGATE and [
                    s for s in structure_dict[structure_type] if not s.is_ready
                ]:
                    almost_ready = True
                    break

                for s in structure_dict[structure_type]:
                    if s.orders:
                        if s.orders[0].progress >= self.unit_pending_progress:
                            almost_ready = True
                            break
                    # structure about to come online
                    if 1.0 > s.build_progress >= self.unit_pending_progress:
                        almost_ready = True
                        break

            if almost_ready:
                continue

            priority: int = army_comp_info["priority"]
            assert 0 <= priority < 11, (
                f"Priority for {unit_type_id} is set to {priority},"
                f"it should be an integer between 0 - 10."
                f"Where 0 has highest priority."
            )

            # add max depending on income
            max_pending = int(collection_rate / 1000)

            if ai.structure_pending(trained_from) >= max_pending:
                continue

            built = BuildStructure(self.base_location, trained_from).execute(
                ai, ai.config, ai.mediator
            )
            if built:
                logger.info(
                    f"Adding {trained_from} so that we can build "
                    f"more {unit_type_id}. Current proportion: {current_proportion}"
                    f" Target proportion: {target_proportion}"
                )
            return built

        # this would mean we went through the main for loop
        # and didn't do anything
        return False

    @staticmethod
    def _not_started_but_in_building_tracker(
        ai: "AresBot", mediator: ManagerMediator, structure_type: UnitID
    ) -> bool:
        """
        Figures out if worker in on route to build something, and
        that structure_type doesn't exist yet.

        Parameters
        ----------
        ai
        mediator
        structure_type

        Returns
        -------

        """
        building_tracker: dict = mediator.get_building_tracker_dict
        for tag, info in building_tracker.items():
            structure_id: UnitID = building_tracker[tag][ID]
            if structure_id != structure_type:
                continue

            target: Point2 = building_tracker[tag][TARGET]

            if not ai.structures.filter(
                lambda s: cy_distance_to_squared(s.position, target.position) < 1.0
            ):
                return True

        return False

    def _teching_up(
        self, ai: "AresBot", unit_type_id: UnitID, trained_from: UnitID
    ) -> bool:
        structures_dict: dict = ai.mediator.get_own_structures_dict
        tech_required: list[UnitID] = UNIT_TECH_REQUIREMENT[unit_type_id]
        without_techlabs: list[UnitID] = [s for s in tech_required if s not in ADD_ONS]
        _trained_from: list[Unit] = structures_dict[trained_from].copy()
        if unit_type_id in GATEWAY_UNITS:
            _trained_from.extend(structures_dict[UnitID.WARPGATE])

        for structure_type in UNIT_TECH_REQUIREMENT[unit_type_id]:
            if ai.structure_pending(structure_type):
                continue

            checks: list[UnitID] = [structure_type]
            if structure_type == UnitID.GATEWAY:
                checks.append(UnitID.WARPGATE)

            if any(ai.structure_present_or_pending(check) for check in checks):
                continue

            if structure_type in TECHLAB_TYPES:
                if not ai.can_afford(structure_type):
                    continue
                can_add_tech_lab: bool = True
                # there might be idle structure with tech lab anyway
                # can't be used since tech structures not present
                if len([s for s in _trained_from if s.has_techlab and s.is_idle]) > 0:
                    can_add_tech_lab = False
                else:
                    for type_id in without_techlabs:
                        if len(structures_dict[type_id]) == 0:
                            can_add_tech_lab = False

                if not can_add_tech_lab:
                    continue

                if base_structures := [
                    s
                    for s in _trained_from
                    if s.is_ready and s.is_idle and not s.has_add_on
                ]:
                    base_structures[0].build(structure_type)
                    logger.info(
                        f"Adding {structure_type} so that we can "
                        f"build more {unit_type_id}"
                    )
                    return True

            # found something to build?
            elif ai.tech_requirement_progress(structure_type) == 1.0:
                building: bool = BuildStructure(
                    self.base_location, structure_type
                ).execute(ai, ai.config, ai.mediator)
                if building:
                    logger.info(
                        f"Adding {structure_type} so that we "
                        f"can build more {unit_type_id}"
                    )
                return building

        return False
