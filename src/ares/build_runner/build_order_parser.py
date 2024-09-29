from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable, Optional, Union

import numpy as np
from cython_extensions import cy_towards, cy_unit_pending
from loguru import logger
from map_analyzer import MapData, Region
from sc2.data import Race
from sc2.dicts.unit_trained_from import UNIT_TRAINED_FROM
from sc2.dicts.upgrade_researched_from import UPGRADE_RESEARCHED_FROM
from sc2.game_data import Cost
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId as UnitID
from sc2.ids.upgrade_id import UpgradeId
from sc2.position import Point2

if TYPE_CHECKING:
    from ares import AresBot

from ares.build_runner.build_order_step import BuildOrderStep
from ares.consts import ALL_STRUCTURES, BuildOrderOptions, BuildOrderTargetOptions


@dataclass
class BuildOrderParser:
    """Parses a build order string into a list of `BuildOrderStep`.

    Attributes:
    -----------
    ai: `AresBot`
        The bot instance.
    build_order_step_dict: Optional[Dict]
        A dictionary of `BuildOrderStep` objects representing
        the recognized build order commands.

    Methods:
    --------
    parse() -> List[BuildOrderStep]:
        Parses the `raw_build_order` attribute into a list of `BuildOrderStep`.
    """

    ai: "AresBot"
    build_order_step_dict: dict = None

    def __post_init__(self) -> None:
        """Initializes the `build_order_step_dict` attribute."""
        self.build_order_step_dict = self._generate_build_step_dict()

    def parse(
        self, raw_build_order: list[str], remove_completed: bool = False
    ) -> list[BuildOrderStep]:
        """Parses the `raw_build_order` attribute into a list of `BuildOrderStep`.

        Returns:
        --------
        List[BuildOrderStep]
            The list of `BuildOrderStep` objects parsed from `raw_build_order`.
        """
        build_order: list[BuildOrderStep] = []
        for raw_step in raw_build_order:
            if isinstance(raw_step, str):
                build_order = self._parse_string_command(raw_step, build_order)
            elif isinstance(raw_step, dict):
                build_order = self._parse_dict_command(raw_step, build_order)

        # incase we switched from a different build
        if remove_completed:
            build_order = self._remove_completed_steps(build_order)
        return build_order

    def _generate_build_step_dict(self) -> dict:
        """Generates a dictionary of `BuildOrderStep` objects representing the
        recognized build order commands.

        Returns:
        --------
        Dict
            A dictionary of `BuildOrderStep` objects representing the recognized
            build order commands.
        """
        min_minerals_for_expand: int = 185 if self.ai.race == Race.Zerg else 285
        return {
            BuildOrderOptions.CHRONO: lambda: BuildOrderStep(
                command=AbilityId.EFFECT_CHRONOBOOST,
                start_condition=lambda: lambda: any(
                    [t.energy >= 50 for t in self.ai.townhalls]
                ),
                end_condition=lambda: True,
            ),
            BuildOrderOptions.EXPAND: lambda: BuildOrderStep(
                command=self.ai.base_townhall_type,
                start_condition=lambda: self.ai.minerals >= min_minerals_for_expand,
                end_condition=lambda: self.ai.structures.filter(
                    lambda s: 0.00001 <= s.build_progress < 0.05
                    and s.type_id == self.ai.base_townhall_type
                ),
            ),
            BuildOrderOptions.GAS: lambda: BuildOrderStep(
                command=self.ai.gas_type,
                start_condition=lambda: self.ai.minerals >= 0
                if self.ai.race == Race.Zerg
                else 50,
                end_condition=lambda: self.ai.structures.filter(
                    lambda s: 0.00001 <= s.build_progress < 0.05
                    and s.type_id == self.ai.gas_type
                ),
            ),
            BuildOrderOptions.ORBITAL: lambda: BuildOrderStep(
                command=AbilityId.UPGRADETOORBITAL_ORBITALCOMMAND,
                start_condition=lambda: self.ai.minerals >= 150
                and self.ai.tech_requirement_progress(UnitID.ORBITALCOMMAND) == 1.0
                and self.ai.townhalls.filter(lambda th: th.is_ready and th.is_idle),
                end_condition=lambda: True,
            ),
            BuildOrderOptions.OVERLORD_SCOUT: lambda: BuildOrderStep(
                BuildOrderOptions.OVERLORD_SCOUT,
                lambda: self.ai.mediator.get_own_army_dict[UnitID.OVERLORD],
                # confident the start condition will auto make the end condition == True
                lambda: True,
            ),
            BuildOrderOptions.SUPPLY: lambda: BuildOrderStep(
                command=self.ai.supply_type,
                start_condition=lambda: self.ai.can_afford(self.ai.supply_type)
                if self.ai.race == Race.Zerg
                else self.ai.minerals >= 25,
                end_condition=lambda: True
                if self.ai.race == Race.Zerg
                else (
                    self.ai.structures.filter(
                        lambda s: 0.00001 <= s.build_progress < 0.05
                        and s.type_id == self.ai.supply_type
                    )
                ),
            ),
            BuildOrderOptions.WORKER: lambda: BuildOrderStep(
                self.ai.worker_type,
                lambda: self._can_train_unit(self.ai.worker_type),
                # confident the start condition will auto make the end condition == True
                lambda: True,
            ),
            BuildOrderOptions.WORKER_SCOUT: lambda: BuildOrderStep(
                BuildOrderOptions.WORKER_SCOUT,
                lambda: self.ai.workers,
                # confident the start condition will auto make the end condition == True
                lambda: True,
            ),
        }

    def _generate_structure_build_step(self, structure_id: UnitID) -> Callable:
        """Generic method to add any structure to a build order.

        Parameters
        ----------
        structure_id :
            The type of structure we wish to build.

        Returns
        -------
        BuildOrderStep :
            A new build step to put in a build order.
        """
        cost: Cost = self.ai.calculate_cost(structure_id)
        return lambda: BuildOrderStep(
            command=structure_id,
            start_condition=lambda: self.ai.minerals >= cost.minerals - 75
            and self.ai.vespene >= cost.vespene - 25,
            # set via on_structure_started hook
            end_condition=lambda: False,
        )

    def _generate_unit_build_step(self, unit_id: UnitID) -> Callable:
        """Generic method to add any unit to a build order.

        Parameters
        ----------
        unit_id :
            The type of unit we wish to train.

        Returns
        -------
        BuildOrderStep :
            A new build step to put in a build order.
        """
        trained_from: set[UnitID]
        if unit_id == UnitID.ARCHON:
            trained_from = {UnitID.DARKTEMPLAR, UnitID.HIGHTEMPLAR}
        else:
            trained_from = UNIT_TRAINED_FROM[unit_id]

        check_supply_cost: bool = unit_id not in {UnitID.ARCHON, UnitID.BANELING}
        return lambda: BuildOrderStep(
            command=unit_id,
            start_condition=lambda: (
                self.ai.can_afford(unit_id, check_supply_cost=check_supply_cost)
                or unit_id == UnitID.ARCHON
            )
            and self.ai.tech_ready_for_unit(unit_id)
            and len(self.ai.get_build_structures(trained_from, unit_id)) > 0,
            # if start condition is True a train order will be issued
            # therefore it will automatically complete the step
            end_condition=lambda: unit_id != UnitID.ARCHON,
        )

    def _generate_upgrade_build_step(self, upgrade_id: UpgradeId) -> Callable:
        """Generic method to add any upgrade to a build order.

        Parameters
        ----------
        upgrade_id :
            The type of unit we wish to train.

        Returns
        -------
        BuildOrderStep :
            A new build step to put in a build order.
        """
        researched_from: UnitID = UPGRADE_RESEARCHED_FROM[upgrade_id]
        return lambda: BuildOrderStep(
            command=upgrade_id,
            start_condition=lambda: self.ai.can_afford(upgrade_id)
            and not self.ai.already_pending_upgrade(upgrade_id)
            and len(
                [
                    s
                    for s in self.ai.structures
                    if s.is_ready and s.is_idle and s.type_id == researched_from
                ]
            )
            > 0,
            # if start condition is True a train order will be issued
            # therefore it will automatically complete the step
            end_condition=lambda: self.ai.pending_or_complete_upgrade(upgrade_id),
        )

    def _can_train_unit(self, unit_type: UnitID) -> bool:
        """Quick check if a unit can be trained.

        Used specific for strict opening build orders and is not reusable.
        Since this doesn't check if a structure already has a train order.

        Parameters
        ----------
        unit_type :
            The type of unit we wish to train.

        Returns
        -------
        bool :
            Whether we have resources, supply and structure to train unit_type.
        """
        if self.ai.all_own_units.filter(
            lambda u: u.type_id in UNIT_TRAINED_FROM[unit_type]
            and u.build_progress == 1.0
            and u.is_idle
        ):
            return self.ai.can_afford(unit_type)

        return False

    def _parse_string_command(
        self, raw_step: str, build_order: list[BuildOrderStep]
    ) -> list[BuildOrderStep]:
        commands: list[str] = raw_step.split(" ")

        supply: int
        command: str
        supply, command = self._get_supply_and_command(raw_step)

        # if a user passed a command matching a UnitTypeID enum key
        # then automatically handle that
        try:
            unit_id_command: UnitID = UnitID[command]
            if unit_id_command in ALL_STRUCTURES:
                step: BuildOrderStep = self._generate_structure_build_step(
                    unit_id_command
                )()
            else:
                step: BuildOrderStep = self._generate_unit_build_step(unit_id_command)()
        except Exception:
            try:
                upgrade_id_command: UpgradeId = UpgradeId[command]
                step: BuildOrderStep = self._generate_upgrade_build_step(
                    upgrade_id_command
                )()
            except Exception:
                assert BuildOrderOptions.contains_key(
                    command
                ), f"Unrecognized build order command, got: {command}"
                step: BuildOrderStep
                if command == BuildOrderOptions.CORE:
                    step = self._generate_structure_build_step(UnitID.CYBERNETICSCORE)()
                elif command == BuildOrderOptions.GATE:
                    step = self._generate_structure_build_step(UnitID.GATEWAY)()
                else:
                    step = self.build_order_step_dict[BuildOrderOptions[command]]()

                if command == BuildOrderOptions.WORKER_SCOUT:
                    step.target = self._get_main_scouting_points(
                        BuildOrderTargetOptions.ENEMY_SPAWN, []
                    )

        if not step:
            return build_order

        # how many of this step to add?
        # incase user passes `stalker x3` or something
        duplicates: int = 1
        # check extra command arguments like ``expand @ natural``
        if len(commands) >= 2:
            extra_commands: list[str] = commands[2:]
            for command in extra_commands:
                target = command.upper()
                # Try to set the target
                if _target := self._get_target_for_step(target):
                    step.target = _target

                # Extract integer from the target if applicable
                if _duplicates := self.extract_integer_from_target(target):
                    duplicates = _duplicates

        if command == BuildOrderOptions.CHRONO and not step.target:
            raise Exception(
                f"No target found for chrono build step command. \n"
                f"Valid example: "
                f"``` 16 chrono @ nexus ``` \n"
                f"Found: {raw_step}"
            )

        step.start_at_supply = supply
        for i in range(duplicates):
            build_order.append(step)
        return build_order

    def _parse_dict_command(
        self, raw_step: dict, build_order: list[BuildOrderStep]
    ) -> list[BuildOrderStep]:
        for commands, targets in raw_step.items():
            supply: int
            command: str
            supply, command = self._get_supply_and_command(commands)

            assert BuildOrderOptions.contains_key(
                command
            ), f"Unrecognized build order command, got: {command}"

            step: BuildOrderStep = self.build_order_step_dict[
                BuildOrderOptions[command]
            ]()
            step.start_at_supply = supply

            assert isinstance(targets, list), (
                f"Build order commands using dicts should have a list type as the "
                f"value, got {type(targets)}. "
                f" Please check the following command in your build order: {raw_step}"
            )
            _target: str
            target_positions: list[Point2] = []
            for target in targets:
                _target: str = target.upper()
                assert BuildOrderTargetOptions.contains_key(_target), (
                    f"Unrecognized build order target option, got: {_target}."
                    f"Valid options are: {BuildOrderTargetOptions.list_options()}"
                )
                order_target: BuildOrderTargetOptions = BuildOrderTargetOptions[_target]
                # scout around main bases
                if order_target in {
                    BuildOrderTargetOptions.SPAWN,
                    BuildOrderTargetOptions.ENEMY_SPAWN,
                }:
                    target_positions = self._get_main_scouting_points(
                        order_target, target_positions
                    )

                # look behind natural
                elif order_target == BuildOrderTargetOptions.NAT:
                    location: Point2 = self._get_target(order_target)
                    behind_min_line_points: list[
                        Point2
                    ] = self.ai.mediator.get_behind_mineral_positions(th_pos=location)
                    for point in behind_min_line_points:
                        target_positions.append(point)
                # otherwise just go to location
                else:
                    target_positions.append(self._get_target(order_target))

            step.target = target_positions

            build_order.append(step)

        return build_order

    @staticmethod
    def extract_integer_from_target(target: str) -> Optional[int]:
        """Extract integer from target if it starts with 'X'."""
        if target.startswith("X") or target.startswith("*"):
            try:
                return int(target[1:])
            except ValueError as e:
                print(f"Error: {e}")
        return None

    @staticmethod
    def _get_target_for_step(target: str) -> Union[str, UnitID]:
        """Set the target for the step."""
        try:
            if target == BuildOrderOptions.CORE:
                return UnitID.CYBERNETICSCORE
            else:
                return UnitID[target]
        except KeyError:
            try:
                return BuildOrderTargetOptions[target]
            except KeyError:
                pass

    @staticmethod
    def _get_supply_and_command(raw_step: str) -> tuple[int, str]:
        """
        Parse the initial part of the build order command, which
        should always be something like:

        `13 supply`

        Parameters
        ----------
        raw_step

        Returns
        -------

        """
        commands: list[str] = raw_step.split(" ")
        assert (
            len(commands) >= 2
        ), f"Expected 2 or more words in build order command, got {raw_step}"
        # supply at which to start
        try:
            supply: int = int(commands[0])
        except ValueError:
            logger.warning(
                f"""{raw_step} should begin with an integer supply count,
                found {commands[0]}, setting supply target to 0"""
            )
            supply: int = 0

        # this is the main command of a build order step (worker, gas, expand etc)
        command: str = commands[1].upper()

        return supply, command

    def _get_main_scouting_points(
        self, order_target: BuildOrderTargetOptions, target_positions: list[Point2]
    ) -> list[Point2]:
        location: Point2 = self._get_target(order_target)
        behind_min_line: Point2 = self.ai.mediator.get_behind_mineral_positions(
            th_pos=location
        )[1]
        if order_target == BuildOrderTargetOptions.ENEMY_SPAWN:
            target_positions.append(behind_min_line)

        # Using region perimeter to get some scout points
        # filter out areas by ramp and minerals as don't need to check there
        map_data: MapData = self.ai.mediator.get_map_data_object
        region: Region = map_data.in_region_p(location)
        perimeter: np.ndarray = region.perimeter
        ramp_point: Point2 = region.region_ramps[0].top_center.rounded
        ramp_point_array = np.array([ramp_point.x, ramp_point.y])
        distances = np.linalg.norm(perimeter - ramp_point_array, axis=1)
        filtered_points = perimeter[distances > 8.0]
        distances = np.linalg.norm(
            filtered_points - np.array([behind_min_line.x, behind_min_line.y]),
            axis=1,
        )
        filtered_points = filtered_points[distances > 10.0]

        # Number of points
        n = len(filtered_points)
        _step = n // 6
        indices = [(i * _step) % n for i in range(6)]
        for point in filtered_points[indices]:
            target_positions.append(Point2(point))

        return target_positions

    def _get_target(self, target: Optional[str]) -> Point2:
        match target:
            case BuildOrderTargetOptions.ENEMY_FOURTH:
                return self.ai.mediator.get_enemy_expansions[2][0]
            case BuildOrderTargetOptions.ENEMY_NAT:
                return self.ai.mediator.get_enemy_nat
            case BuildOrderTargetOptions.ENEMY_NAT_HG_SPOT:
                return self.ai.mediator.get_closest_overlord_spot(
                    from_pos=Point2(
                        cy_towards(
                            self.ai.mediator.get_enemy_nat,
                            self.ai.game_info.map_center,
                            10.0,
                        )
                    )
                )
            case BuildOrderTargetOptions.ENEMY_NAT_VISION:
                return Point2(
                    cy_towards(
                        self.ai.mediator.get_enemy_nat,
                        self.ai.game_info.map_center,
                        10.0,
                    )
                )
            case BuildOrderTargetOptions.ENEMY_RAMP:
                return self.ai.mediator.get_enemy_ramp.top_center
            case BuildOrderTargetOptions.ENEMY_SPAWN:
                return self.ai.enemy_start_locations[0]
            case BuildOrderTargetOptions.ENEMY_THIRD:
                return self.ai.mediator.get_enemy_expansions[1][0]
            case BuildOrderTargetOptions.FIFTH:
                return self.ai.mediator.get_own_expansions[3][0]
            case BuildOrderTargetOptions.FOURTH:
                return self.ai.mediator.get_own_expansions[2][0]
            case BuildOrderTargetOptions.MAP_CENTER:
                return self.ai.game_info.map_center
            case BuildOrderTargetOptions.NAT:
                return self.ai.mediator.get_own_nat
            case BuildOrderTargetOptions.RAMP:
                return self.ai.main_base_ramp.top_center
            case BuildOrderTargetOptions.SIXTH:
                return self.ai.mediator.get_own_expansions[4][0]
            case BuildOrderTargetOptions.SPAWN:
                return self.ai.start_location
            case BuildOrderTargetOptions.THIRD:
                return self.ai.mediator.get_own_expansions[1][0]
        return self.ai.start_location

    def _remove_completed_steps(
        self, build_order: list[BuildOrderStep]
    ) -> list[BuildOrderStep]:
        """
        Provided a build order, look for steps already completed.
        This is useful when switching from one opening to another.

        Parameters
        ----------
        build_order

        Returns
        -------

        """
        indices_to_remove: list[int] = []

        num_same_steps_found: dict[UnitID, int] = defaultdict(int)
        # pretend we already built things we spawn with
        # makes working this out easier
        num_same_steps_found[self.ai.base_townhall_type] = 1
        num_same_steps_found[UnitID.OVERLORD] = 1
        num_same_steps_found[self.ai.worker_type] = 12

        for i, step in enumerate(build_order):
            command: Union[AbilityId, UnitID, UpgradeId] = step.command
            if command == BuildOrderOptions.WORKER_SCOUT:
                logger.info(
                    f"Removing {command} from build order. "
                    f"Please note worker scouts are always "
                    f"removed when switching build orders"
                )
                indices_to_remove.append(i)

            # remove any steps that chrono the nexus
            # not ideal but helps build order not getting stuck
            elif isinstance(command, AbilityId):
                if (
                    command == AbilityId.EFFECT_CHRONOBOOST
                    and step.target == UnitID.NEXUS
                ):
                    logger.info(f"Removing {command} from build order")
                    indices_to_remove.append(i)
            elif isinstance(command, UnitID):
                if command in ALL_STRUCTURES:
                    num_existing: int = len(
                        self.ai.mediator.get_own_structures_dict[command]
                    )
                    on_route: int = int(
                        self.ai.not_started_but_in_building_tracker(command)
                    )
                    total_present: int = num_existing + on_route
                else:
                    num_units: int = len(self.ai.mediator.get_own_army_dict[command])
                    pending: int = cy_unit_pending(self.ai, command)
                    total_present: int = num_units + pending

                if total_present == 0:
                    continue

                # while there are less of these steps then what are present
                if num_same_steps_found[command] < total_present:
                    logger.info(f"Removing {command} from build order")
                    num_same_steps_found[command] += 1
                    indices_to_remove.append(i)

            elif isinstance(command, UpgradeId):
                if self.ai.pending_or_complete_upgrade(command):
                    logger.info(f"Removing {command} from build order")
                    indices_to_remove.append(i)

        for index in sorted(indices_to_remove, reverse=True):
            del build_order[index]

        return build_order
