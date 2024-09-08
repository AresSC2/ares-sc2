from dataclasses import dataclass, field
from math import isclose
from typing import TYPE_CHECKING, Optional

from cython_extensions import cy_sorted_by_distance_to
from sc2.dicts.unit_trained_from import UNIT_TRAINED_FROM
from sc2.game_data import Cost
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId as UnitID
from sc2.ids.upgrade_id import UpgradeId
from sc2.position import Point2
from sc2.unit import Unit

if TYPE_CHECKING:
    from ares import AresBot

from ares.behaviors.macro.macro_behavior import MacroBehavior
from ares.consts import UnitRole
from ares.managers.manager_mediator import ManagerMediator


@dataclass
class SpawnController(MacroBehavior):
    """Handle spawning army compositions.

    Example bot code:
    ```py
    from ares.behaviors.spawn_controller import SpawnController

    # Note: This does not try to build production facilities and
    # will ignore units that are impossible to currently spawn.
    army_composition: dict[UnitID: {float, bool}] = {
        UnitID.MARINE: {"proportion": 0.6, "priority": 2},  # lowest priority
        UnitID.MEDIVAC: {"proportion": 0.25, "priority": 1},
        UnitID.SIEGETANK: {"proportion": 0.15, "priority": 0},  # highest priority
    }
    # where `self` is an `AresBot` object
    self.register_behavior(SpawnController(army_composition))

    ```

    Attributes
    ----------
    army_composition_dict : dict[UnitID: float, bool]
        A dictionary that details how an army composition should be made up.
        The proportional values should all add up to 1.0.
        With a priority integer to give units emphasis.
    freeflow_mode : bool (default: False)
        If set to True, army comp proportions are ignored, and resources
        will be spent freely.
    ignore_proportions_below_unit_count : int (default 0)
        In early game units effect the army proportions significantly.
        This allows some units to be freely built before proportions are respected.
    over_produce_on_low_tech : bool (default True)
        If there is only tech available for one unit, this will allow this
        unit to be constantly produced.
    ignored_build_from_tags : set[int]
        Prevent spawn controller from morphing from these tags
        Example: Prevent selecting barracks that needs to build an addon
    maximum : int (default 20)
        The maximum unit type we can produce in a single step.
    spawn_target : Union[Point2, None] (default None)
        Prioritize spawning units near this location.

    """

    army_composition_dict: dict[UnitID, dict[str, float, str, int]]
    freeflow_mode: bool = False
    ignore_proportions_below_unit_count: int = 0
    over_produce_on_low_tech: bool = True
    ignored_build_from_tags: set[int] = field(default_factory=set)
    maximum: int = 20
    spawn_target: Optional[Point2] = None

    # key: Unit that should get a build order, value: what UnitID to build
    __build_dict: dict[Unit, UnitID] = field(default_factory=dict)
    # already used tags
    __excluded_structure_tags: set[int] = field(default_factory=set)
    __supply_available: float = 0.0

    def execute(self, ai: "AresBot", config: dict, mediator: ManagerMediator) -> bool:
        # allow gateways to morph before issuing commands
        if UpgradeId.WARPGATERESEARCH in ai.state.upgrades and [
            g
            for g in mediator.get_own_structures_dict[UnitID.GATEWAY]
            if g.is_ready and g.is_idle
        ]:
            return False

        self.__supply_available = ai.supply_left

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

        check_proportion: bool = True
        proportion_sum: float = 0.0
        # remember units that meet tech requirement
        units_ready_to_build: list[UnitID] = []
        # keep track of what units we have tech for
        tech_ready_for: list[UnitID] = []
        # iterate through desired army comp starting with the highest priority unit
        for unit_type_id, army_comp_info in sorted(
            army_comp_dict.items(), key=lambda x: x[1].get("priority", int(0))
        ):
            assert isinstance(unit_type_id, UnitID), (
                f"army_composition_dict expects UnitTypeId type as keys, "
                f"got {type(unit_type_id)}"
            )
            priority: int = army_comp_info["priority"]
            assert 0 <= priority < 11, (
                f"Priority for {unit_type_id} is set to {priority},"
                f"it should be an integer between 0 - 10."
                f"Where 0 has highest priority."
            )

            target_proportion: float = army_comp_info["proportion"]
            proportion_sum += target_proportion

            # work out if we are able to produce this unit
            if not ai.tech_ready_for_unit(unit_type_id):
                continue

            tech_ready_for.append(unit_type_id)

            trained_from: set[UnitID]
            if unit_type_id == UnitID.ARCHON:
                trained_from = {UnitID.HIGHTEMPLAR, UnitID.DARKTEMPLAR}
            else:
                trained_from = UNIT_TRAINED_FROM[unit_type_id]

            # get all idle build structures/units we can create this unit from
            build_structures: list[Unit] = ai.get_build_structures(
                trained_from,
                unit_type_id,
                self.__build_dict,
                self.ignored_build_from_tags,
            )
            # there is no possible way to build this unit, skip even if higher priority
            if len(build_structures) == 0:
                continue

            # archon is a special case that can't be handled generically
            if unit_type_id == UnitID.ARCHON:
                self._handle_archon_morph(ai, build_structures, mediator)
                continue

            # prioritize spawning close to spawn target
            if self.spawn_target:
                build_structures = cy_sorted_by_distance_to(
                    build_structures, self.spawn_target
                )

            # can't afford unit?
            # then we might want to break out loop till we can afford
            if not self._can_afford(ai, unit_type_id):
                if (
                    self.freeflow_mode
                    or num_total_units < self.ignore_proportions_below_unit_count
                ):
                    continue
                # break out the loop, don't spend resources on lower priority units
                else:
                    check_proportion = False
                    break

            # keep track of which unit types the build_structures/ tech is ready for
            units_ready_to_build.append(unit_type_id)

            num_this_unit: int = mediator.get_own_unit_count(unit_type_id=unit_type_id)
            current_proportion: float = num_this_unit / (num_total_units + 1e-16)
            # already have enough of this unit type,
            # but we could add it if:
            # freeflow mode or we don't have much army yet
            if (
                current_proportion >= target_proportion
                and not self.freeflow_mode
                and num_total_units >= self.ignore_proportions_below_unit_count
            ):
                continue

            amount, supply, cost = self._calculate_build_amount(
                ai,
                unit_type_id,
                build_structures,
                self.__supply_available,
                self.maximum,
            )
            self._add_to_build_dict(
                ai, unit_type_id, build_structures, amount, supply, cost
            )
        # if we can only build one type of unit, keep adding them
        if (
            len(tech_ready_for) == 1
            and self.over_produce_on_low_tech
            and len(units_ready_to_build) > 0
            and self.maximum > 1
        ):
            build_structures = ai.get_build_structures(
                UNIT_TRAINED_FROM[units_ready_to_build[0]],
                units_ready_to_build[0],
                self.__build_dict,
                self.ignored_build_from_tags,
            )
            amount, supply, cost = self._calculate_build_amount(
                ai, units_ready_to_build[0], build_structures, self.__supply_available
            )
            # prioritize spawning close to spawn target
            if self.spawn_target:
                build_structures = cy_sorted_by_distance_to(
                    build_structures, self.spawn_target
                )
            self._add_to_build_dict(
                ai, units_ready_to_build[0], build_structures, amount, supply, cost
            )

        if check_proportion and not self.freeflow_mode:
            assert isclose(
                proportion_sum, 1.0
            ), f"The army comp proportions should equal 1.0, got {proportion_sum}"

        return self._morph_units(ai, mediator)

    def _add_to_build_dict(
        self,
        ai: "AresBot",
        type_id: UnitID,
        base_unit: list[Unit],
        amount: int,
        supply_cost: float,
        cost_per_unit: Cost,
    ) -> None:
        """Execute the spawn controller task (Called from `behavior_executioner.py`).

        Handle unit production as per the .........

        Parameters
        ----------
        ai :
            Bot object that will be running the game
        type_id :
            Type of unit we want to spawn.
        base_unit :
            Unit objects we can spawn this unit from.
        amount :
            How many type_id we intend to spawn.
        supply_cost :
            Supply cost of spawning type_id amount.
        cost_per_unit :
            Minerals and vespene cost.
        """
        # min check to make sure we don't pop from empty lists
        for _ in range(min(len(base_unit), amount)):
            self.__build_dict[base_unit.pop(0)] = type_id
            ai.minerals -= cost_per_unit.minerals
            ai.vespene -= cost_per_unit.vespene
            self.__supply_available -= supply_cost

    @staticmethod
    def _calculate_build_amount(
        ai: "AresBot",
        unit_type: UnitID,
        base_units: list[Unit],
        supply_left: float,
        maximum: int = 20,
    ) -> tuple[int, float, Cost]:
        """Execute the spawn controller task (Called from `behavior_executioner.py`).

        Handle unit production as per the .........

        Parameters
        ----------
        ai :
            Bot object that will be running the game
        unit_type :
            Type of unit we want to spawn.
        base_units :
            Unit objects we can spawn this unit from.
        supply_left :
            How much total supply we have available.
        maximum :
            A limit on how many units can be spawned in one go.
        """
        cost = ai.cost_dict[unit_type]
        supply_cost = ai.calculate_supply_cost(unit_type)
        amount = min(
            int(ai.minerals / cost.minerals) if cost.minerals else 9999999,
            int(ai.vespene / cost.vespene) if cost.vespene else 9999999,
            int(supply_left / supply_cost) if supply_cost else 9999999,
            len(base_units),
            maximum,
        )
        return amount, supply_cost, cost

    @staticmethod
    def _can_afford(ai: "AresBot", unit_type_id: UnitID) -> bool:
        if unit_type_id == UnitID.ARCHON:
            return True
        return ai.can_afford(unit_type_id)

    @staticmethod
    def _handle_archon_morph(
        ai: "AresBot", build_structures: list[Unit], mediator: ManagerMediator
    ) -> None:
        unit_role_dict: dict[UnitRole, set] = mediator.get_unit_role_dict
        build_structures = [
            b
            for b in build_structures
            if b.tag not in unit_role_dict[UnitRole.MORPHING] and b.is_ready
        ]
        if len(build_structures) < 2:
            return

        templar: list[Unit] = build_structures[:2]
        ai.request_archon_morph(templar)

    def _morph_units(self, ai: "AresBot", mediator: ManagerMediator) -> bool:
        did_action: bool = False
        for unit, value in self.__build_dict.items():
            did_action = True
            mediator.clear_role(tag=unit.tag)
            if value == UnitID.BANELING:
                unit(AbilityId.MORPHTOBANELING_BANELING)
            elif value == UnitID.RAVAGER:
                unit(AbilityId.MORPHTORAVAGER_RAVAGER)
            # prod building is warp gate, but we really
            # want to spawn from psionic field
            elif unit.type_id == UnitID.WARPGATE:
                mediator.request_warp_in(
                    build_from=unit, unit_type=value, target=self.spawn_target
                )
            else:
                unit.train(value)
                ai.num_larva_left -= 1

        return did_action
