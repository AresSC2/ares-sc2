from dataclasses import dataclass
from typing import TYPE_CHECKING

from cython_extensions import cy_distance_to_squared
from loguru import logger
from sc2.data import Race
from sc2.dicts.unit_trained_from import UNIT_TRAINED_FROM
from sc2.dicts.unit_unit_alias import UNIT_UNIT_ALIAS
from sc2.game_data import Cost
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
    add_production_at_bank : Tuple[int, int], optional
        When we reach this bank size, work out what extra production
        would be useful.
        Tuple where first value is minerals and second is vespene.
        (default = `(300, 300)`)
    alpha : float, optional
        Controls how much production to add when bank is
        higher than `add_production_at_bank`.
        (default = `0.9`)
    unit_pending_progress : float, optional
        Check for production structures almost ready
        For example a marine might almost be ready, meaning
        we don't need to add extra production just yet.
         (default = 0.8)
    ignore_below_proportion: float, optional
        If we don't want many of this unit, no point adding production.
        Will check if possible to build unit first.
        Default is `0.05`
    should_repower_structures: bool, optional
        Search for unpowered structures, and build a new
        pylon as needed.
        Default is `True`
    """

    army_composition_dict: dict[UnitID, dict[str, float, str, int]]
    base_location: Point2
    add_production_at_bank: tuple[int, int] = (300, 300)
    alpha: float = 0.9
    unit_pending_progress: float = 0.75
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

        num_total_units: int = sum(
            [
                mediator.get_own_unit_count(unit_type_id=unit_type)
                for unit_type in unit_types
            ]
        )
        proportion_sum: float = 0.0
        structure_dict: dict[UnitID, Units] = mediator.get_own_structures_dict
        flying_structures: dict[int, dict] = mediator.get_flying_structure_tracker
        # +1 to avoid division by zero
        collection_rate_minerals: int = ai.state.score.collection_rate_minerals + 1
        collection_rate_vespene: int = ai.state.score.collection_rate_vespene + 1

        # iterate through desired army comp starting with the highest priority unit
        for unit_type_id, army_comp_info in sorted(
            army_comp_dict.items(), key=lambda x: x[1].get("priority", int(0))
        ):
            assert isinstance(unit_type_id, UnitID), (
                f"army_composition_dict expects UnitTypeId type as keys, "
                f"got {type(unit_type_id)}"
            )

            num_this_unit: int = mediator.get_own_unit_count(unit_type_id=unit_type_id)
            current_proportion: float = num_this_unit / (num_total_units + 1e-16)
            target_proportion: float = army_comp_info["proportion"]
            proportion_sum += target_proportion
            train_from: set[UnitID] = UNIT_TRAINED_FROM[unit_type_id]
            trained_from: UnitID = next(iter(UNIT_TRAINED_FROM[unit_type_id]))
            if unit_type_id in GATEWAY_UNITS:
                trained_from = UnitID.GATEWAY

            existing_structures: list[Unit] = []
            for structure_type in train_from:
                existing_structures.extend(structure_dict[structure_type])

            # we need to tech up, no further action is required
            if self._teching_up(ai, unit_type_id, trained_from):
                return True

            # we have a worker on route to build this production
            # leave alone for now
            if self._not_started_but_in_building_tracker(ai, mediator, trained_from):
                continue

            # we can afford prod, work out how much prod to support
            # based on income
            if (
                ai.minerals > self.add_production_at_bank[0]
                and ai.vespene > self.add_production_at_bank[1]
            ):
                if self._building_production_due_to_bank(
                    ai,
                    unit_type_id,
                    collection_rate_minerals,
                    collection_rate_vespene,
                    existing_structures,
                    trained_from,
                    target_proportion,
                ):
                    return True

            # target proportion is low and something is pending, don't add extra yet
            if target_proportion <= 0.15 and (
                any([ai.structure_pending(type_id) for type_id in train_from])
            ):
                continue

            # existing production is enough for our income?
            cost: Cost = ai.calculate_cost(unit_type_id)
            total_cost = cost.minerals + cost.vespene
            divide_by: float = total_cost * 4.5
            if len(existing_structures) >= int(
                (collection_rate_minerals + collection_rate_vespene) / divide_by
            ):
                continue

            # if Terran has a production building floating, wait
            if self.is_flying_production(ai, flying_structures, train_from):
                continue

            # already have enough of this unit type, don't need production
            if current_proportion * 1.05 >= target_proportion:
                continue

            # already could build this unit if we wanted to?
            if self._can_already_produce(train_from, structure_dict):
                continue

            # add max depending on income
            max_pending = int(
                (collection_rate_minerals + collection_rate_vespene) / 1000
            )

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

        # we checked everything and no action is required
        return False

    def _building_production_due_to_bank(
        self,
        ai: "AresBot",
        unit_type_id: UnitID,
        collection_rate_minerals: int,
        collection_rate_vespene: int,
        existing_structures: list[Unit],
        trained_from: UnitID,
        target_proportion: float,
    ) -> bool:
        # work out how many units we could afford at once
        cost_of_unit: Cost = ai.calculate_cost(unit_type_id)
        simul_afford_min: int = int(
            (collection_rate_minerals / (cost_of_unit.minerals + 1))
            * self.alpha
            * target_proportion
        )
        simul_afford_ves: int = int(
            (collection_rate_vespene / (cost_of_unit.vespene + 1))
            * self.alpha
            * target_proportion
        )
        num_existing: int = len([s for s in existing_structures if s.is_ready])
        num_production: int = num_existing + ai.structure_pending(trained_from)

        if num_production < simul_afford_min and num_production < simul_afford_ves:
            if BuildStructure(self.base_location, trained_from).execute(
                ai, ai.config, ai.mediator
            ):
                logger.info(f"Adding {trained_from} as income level will support this.")
                return True
        return False

    def _can_already_produce(self, train_from, structure_dict) -> bool:
        for structure_type in train_from:
            if structure_type == UnitID.WARPGATE and [
                s for s in structure_dict[structure_type] if not s.is_ready
            ]:
                return True

            for s in structure_dict[structure_type]:
                if s.is_ready and s.is_idle:
                    return True
                if s.orders:
                    if s.orders[0].progress >= self.unit_pending_progress:
                        return True
                # structure about to come online
                if 1.0 > s.build_progress >= 0.9:
                    return True

        return False

    def is_flying_production(
        self, ai: "AresBot", flying_structures: dict, train_from: set[UnitID]
    ) -> bool:
        if ai.race == Race.Terran:
            prod_flying: bool = False
            # might have this structure flying
            for tag in flying_structures:
                if unit := ai.unit_tag_dict.get(tag, None):
                    # make sure flying structure is nearby
                    if (
                        unit.type_id in UNIT_UNIT_ALIAS
                        and cy_distance_to_squared(unit.position, self.base_location)
                        < 360.0
                    ):
                        for s_id in train_from:
                            if UNIT_UNIT_ALIAS[unit.type_id] == s_id:
                                prod_flying = True
                                break
            if prod_flying:
                return True
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
                        f"tech towards {unit_type_id}"
                    )
                    return True
                continue

            if any(ai.structure_present_or_pending(check) for check in checks):
                continue

            # found something to build?
            elif ai.tech_requirement_progress(structure_type) == 1.0:
                building: bool = BuildStructure(
                    self.base_location, structure_type
                ).execute(ai, ai.config, ai.mediator)
                if building:
                    logger.info(
                        f"Adding {structure_type} so that we "
                        f"can tech towards {unit_type_id}"
                    )
                return building

        return False
