from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import numpy as np
from cython_extensions import cy_towards, cy_unit_pending
from loguru import logger
from map_analyzer import MapData, Region
from sc2.data import Race
from sc2.dicts.unit_trained_from import UNIT_TRAINED_FROM
from sc2.dicts.upgrade_researched_from import UPGRADE_RESEARCHED_FROM
from sc2.game_data import Cost
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId
from sc2.position import Point2

if TYPE_CHECKING:
    from ares import AresBot

from ares.build_runner.build_order_step import BuildOrderStep
from ares.consts import (
    ALL_STRUCTURES,
    TOWNHALL_TYPES,
    BuildOrderOptions,
    BuildOrderTargetOptions,
)


@dataclass
class BuildOrderParser:
    # Non-standard attribute format to bypass PyCharm docstring completion quirks.
    """
    Parses a build order string into a list of `BuildOrderStep`.

    Attributes:
        ai: "Bot Name" : The bot instance.
        build_order_step_dict (build_order_step_dict: dict | None = None :
            A dictionary of `BuildOrderStep` objects representing
            the recognized build order commands.

    Methods:
        parse: Parses the `raw_build_order` attribute into a list of `BuildOrderStep`.
    """

    ai: AresBot
    build_order_step_dict: dict = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        """Initializes the `build_order_step_dict` attribute."""
        self.build_order_step_dict = self._generate_build_step_dict()

    def parse(
        self, raw_build_order: list[str | dict], remove_completed: bool = False
    ) -> list[BuildOrderStep]:
        """
        Parses the `raw_build_order` attribute into a list of `BuildOrderStep`.

        Args:
            raw_build_order (list[str | dict]): Build order extracted from build file.
            remove_completed (bool = False) description

        Returns:
            parsed_build_order list[BuildOrderStep]:
                The list of `BuildOrderStep` objects parsed from `raw_build_order`.

        Raises:
                object_name (object_type) description
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
        dict
            A dictionary of `BuildOrderStep` objects representing the recognized
            build order commands.
        """
        min_minerals_for_expand: int = 130 if self.ai.race == Race.Zerg else 285
        return {
            BuildOrderOptions.CANCEL_GAS: lambda: BuildOrderStep(
                command=AbilityId.CANCEL_BUILDINPROGRESS,
                start_condition=lambda: (
                    lambda: any(
                        g for g in self.ai.gas_buildings if g.build_progress < 1.0
                    )
                ),
                end_condition=lambda: True,
            ),
            BuildOrderOptions.CHRONO: lambda: BuildOrderStep(
                command=AbilityId.EFFECT_CHRONOBOOST,
                start_condition=lambda: (
                    lambda: any(t.energy >= 50 for t in self.ai.townhalls)
                ),
                end_condition=lambda: True,
            ),
            BuildOrderOptions.EXPAND: lambda: BuildOrderStep(
                command=self.ai.base_townhall_type,
                start_condition=lambda: (
                    self.ai.minerals
                    >= min_minerals_for_expand
                    - (300 if len(self.ai.townhalls) >= 2 else 0)
                ),
                end_condition=lambda: self.ai.structures.filter(
                    lambda s: (
                        0.00001 <= s.build_progress < 0.05
                        and s.type_id == self.ai.base_townhall_type
                    )
                ),
            ),
            BuildOrderOptions.GAS: lambda: BuildOrderStep(
                command=self.ai.gas_type,
                start_condition=lambda: (
                    self.ai.minerals >= 0
                    if self.ai.race == Race.Zerg
                    else self.ai.minerals >= 50
                ),
                end_condition=lambda: self.ai.structures.filter(
                    lambda s: (
                        0.00001 <= s.build_progress < 0.05
                        and s.type_id == self.ai.gas_type
                    )
                ),
            ),
            BuildOrderOptions.ORBITAL: lambda: BuildOrderStep(
                command=AbilityId.UPGRADETOORBITAL_ORBITALCOMMAND,
                start_condition=lambda: (
                    self.ai.minerals >= 150
                    and self.ai.tech_requirement_progress(UnitTypeId.ORBITALCOMMAND)
                    == 1.0
                    and self.ai.townhalls.filter(lambda th: th.is_ready and th.is_idle)
                ),
                end_condition=lambda: True,
            ),
            BuildOrderOptions.OVERLORD_SCOUT: lambda: BuildOrderStep(
                BuildOrderOptions.OVERLORD_SCOUT,
                lambda: self.ai.mediator.get_own_army_dict[UnitTypeId.OVERLORD],
                # confident the start condition will auto make the end condition == True
                lambda: True,
            ),
            BuildOrderOptions.SUPPLY: lambda: BuildOrderStep(
                command=self.ai.supply_type,
                start_condition=lambda: (
                    self.ai.can_afford(self.ai.supply_type)
                    if self.ai.race == Race.Zerg
                    else self.ai.minerals >= 25
                ),
                end_condition=lambda: (
                    True
                    if self.ai.race == Race.Zerg
                    else (
                        self.ai.structures.filter(
                            lambda s: (
                                0.00001 <= s.build_progress < 0.05
                                and s.type_id == self.ai.supply_type
                            )
                        )
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

    def _generate_addon_build_step(self, commands) -> Callable:
        # Non-standard attribute format to bypass PyCharm docstring completion quirks.
        """Generates a callable build step for executing an
        `AddonSwap` command in the build runner.

        The `AddonSwap` command allows structures to exchange addon components.
        This function validates the provided command arguments to ensure they
        represent valid structure types before creating a lambda build step for
        execution.

        Args:
            commands (list[str]): List of command parameters.
                The first two parameters are positional, while the last two
                specify the structures involved in the addon swap.

        Raises:
            Exception: If the length of the `commands` list is not exactly 4.
            ValueError: If any structure names provided in the `commands`
                are invalid.

        Returns:
            Callable: A callable object that represents the constructed build step.
        """
        # ['21', 'addonswap', 'factory', 'barracksreactor']
        if len(commands) != 4:
            raise Exception(
                f"Invalid addonswap command in build runner, "
                f"expected 4 arguments, got {len(commands)} \n "
                f"Example: `21 addonswap factory barracksreactor`"
            )
        extra_commands: list[str] = commands[2:]
        add_on_structures: list[UnitTypeId] = []

        invalid: list[str] = []
        for cmd in extra_commands:
            name = cmd.upper()
            unit_type: UnitTypeId = UnitTypeId.__members__.get(name)
            if unit_type is None or unit_type not in ALL_STRUCTURES:
                invalid.append(cmd)
            else:
                add_on_structures.append(unit_type)

        if invalid:
            raise ValueError(
                f"Invalid addonswap command(s): expected structure "
                f"types, got: {', '.join(invalid)}"
            )

        main_structure: UnitTypeId = add_on_structures[0]
        add_on_structure: UnitTypeId = add_on_structures[1]
        structures_dict = self.ai.mediator.get_own_structures_dict
        return lambda: BuildOrderStep(
            command=AbilityId.LIFT,
            start_condition=lambda: (
                len([s for s in structures_dict[main_structure] if s.is_ready]) > 0
                and len([s for s in structures_dict[add_on_structure] if s.is_ready])
                > 0
            ),
            # set via on_structure_started hook
            end_condition=lambda: True,
            target=add_on_structures,
        )

    def _generate_structure_build_step(self, structure_id: UnitTypeId) -> Callable:
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
        _mineral: int = 105 if structure_id in TOWNHALL_TYPES else 75
        if structure_id in {UnitTypeId.LAIR, UnitTypeId.HIVE}:
            upgrade_from: UnitTypeId = (
                UnitTypeId.LAIR
                if structure_id == UnitTypeId.HIVE
                else UnitTypeId.HATCHERY
            )
            return lambda: BuildOrderStep(
                command=(
                    AbilityId.UPGRADETOLAIR_LAIR
                    if structure_id == UnitTypeId.LAIR
                    else AbilityId.UPGRADETOHIVE_HIVE
                ),
                start_condition=lambda: (
                    self.ai.townhalls.filter(
                        lambda th: (
                            th.is_ready and th.is_idle and th.type_id == upgrade_from
                        )
                    )
                    and self.ai.minerals >= cost.minerals
                    and self.ai.vespene >= cost.vespene
                ),
                # set via on_structure_started hook
                end_condition=lambda: True,
            )
        else:
            return lambda: BuildOrderStep(
                command=structure_id,
                start_condition=lambda: (
                    self.ai.minerals >= cost.minerals - _mineral
                    and self.ai.vespene >= cost.vespene - 25
                ),
                # set via on_structure_started hook
                end_condition=lambda: False,
            )

    def _generate_unit_build_step(self, unit_id: UnitTypeId) -> Callable:
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
        trained_from: set[UnitTypeId]
        if unit_id == UnitTypeId.ARCHON:
            trained_from = {UnitTypeId.DARKTEMPLAR, UnitTypeId.HIGHTEMPLAR}
        else:
            trained_from = UNIT_TRAINED_FROM[unit_id]

        check_supply_cost: bool = unit_id not in {
            UnitTypeId.ARCHON,
            UnitTypeId.BANELING,
        }
        return lambda: BuildOrderStep(
            command=unit_id,
            start_condition=lambda: (
                (
                    self.ai.can_afford(unit_id, check_supply_cost=check_supply_cost)
                    or unit_id == UnitTypeId.ARCHON
                )
                and self.ai.tech_ready_for_unit(unit_id)
                and len(self.ai.get_build_structures(trained_from, unit_id)) > 0
            ),
            # if start condition is True a train order will be issued
            # therefore it will automatically complete the step
            end_condition=lambda: unit_id != UnitTypeId.ARCHON,
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
        researched_from: UnitTypeId = UPGRADE_RESEARCHED_FROM[upgrade_id]
        return lambda: BuildOrderStep(
            command=upgrade_id,
            start_condition=lambda: (
                self.ai.can_afford(upgrade_id)
                and not self.ai.already_pending_upgrade(upgrade_id)
                and len(
                    [
                        s
                        for s in self.ai.structures
                        if s.is_ready and s.is_idle and s.type_id == researched_from
                    ]
                )
                > 0
            ),
            # if start condition is True a train order will be issued
            # therefore it will automatically complete the step
            end_condition=lambda: self.ai.pending_or_complete_upgrade(upgrade_id),
        )

    def _can_train_unit(self, unit_type: UnitTypeId) -> bool:
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
            lambda u: (
                u.type_id in UNIT_TRAINED_FROM[unit_type]
                and u.build_progress == 1.0
                and u.is_idle
            )
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

        # if a user passed a command matching a UnitTypeId enum key
        # then automatically handle that
        step: BuildOrderStep
        try:
            unit_id_command: UnitTypeId = UnitTypeId[command]
            if unit_id_command in ALL_STRUCTURES:
                step = self._generate_structure_build_step(unit_id_command)()
            else:
                step = self._generate_unit_build_step(unit_id_command)()
        except Exception:
            try:
                upgrade_id_command: UpgradeId = UpgradeId[command]
                step = self._generate_upgrade_build_step(upgrade_id_command)()
            except Exception:
                assert BuildOrderOptions.contains_key(command), (
                    f"Unrecognized build order command, got: {command}"
                )

                if command == BuildOrderOptions.ADDONSWAP:
                    step = self._generate_addon_build_step(commands)()
                elif command == BuildOrderOptions.CORE:
                    step = self._generate_structure_build_step(
                        UnitTypeId.CYBERNETICSCORE
                    )()
                elif command == BuildOrderOptions.GATE:
                    step = self._generate_structure_build_step(UnitTypeId.GATEWAY)()
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
        if len(commands) >= 2 and command != BuildOrderOptions.ADDONSWAP:
            extra_commands: list[str] = commands[2:]
            for command in extra_commands:
                # build-order strings often use `@` as a separator, e.g.:
                # `13 pylon @ ramp`
                # In that case `raw_step.split(" ")` is ["13","pylon","@","ramp"]
                if command == "@":
                    continue

                # Also support `@ramp` (no space) by stripping a leading "@"
                if command.startswith("@"):
                    command = command[1:]

                target = command.upper()
                # Extract integer from the target if applicable
                # (e.g. `stalker *3` or `drone x4`). These aren't "targets" and
                # shouldn't be sent through `_get_target_for_step`.
                if _duplicates := self.extract_integer_from_target(target):
                    duplicates = _duplicates
                    continue

                # Try to set the target
                try:
                    if _target := self._get_target_for_step(target):
                        step.target = _target
                except ValueError:
                    # Ignore unknown extra tokens; they may be aliases or other
                    # modifiers not relevant to targets.
                    pass

        if command == BuildOrderOptions.CHRONO and not step.target:
            raise Exception(
                f"No target found for chrono build step command. \n"
                f"Valid example: "
                f"``` 16 chrono @ nexus ``` \n"
                f"Found: {raw_step}"
            )

        step.start_at_supply = supply
        for _i in range(duplicates):
            build_order.append(step)
        return build_order

    def _parse_dict_command(
        self, raw_step: dict, build_order: list[BuildOrderStep]
    ) -> list[BuildOrderStep]:
        for commands, targets in raw_step.items():
            supply: int
            command: str
            supply, command = self._get_supply_and_command(commands)

            assert BuildOrderOptions.contains_key(command), (
                f"Unrecognized build order command, got: {command}"
            )

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
                _target = target.upper()
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
                    behind_min_line_points: list[Point2] = (
                        self.ai.mediator.get_behind_mineral_positions(th_pos=location)
                    )
                    for point in behind_min_line_points:
                        target_positions.append(point)
                # otherwise just go to location
                else:
                    target_positions.append(self._get_target(order_target))

            step.target = target_positions

            build_order.append(step)

        return build_order

    @staticmethod
    def extract_integer_from_target(target: str) -> int | None:
        """Extract integer from target if it starts with 'X'."""
        if target.startswith("X") or target.startswith("*"):
            try:
                return int(target[1:])
            except ValueError as e:
                print(f"Error: {e}")
        return None

    @staticmethod
    def _get_target_for_step(target: str) -> str | UnitTypeId:
        """Set the target for the step."""
        try:
            if target == BuildOrderOptions.CORE:
                return UnitTypeId.CYBERNETICSCORE
            else:
                return UnitTypeId[target]
        except KeyError:
            try:
                return BuildOrderTargetOptions[target]
            except KeyError:
                pass
        raise ValueError(f"Unrecognized build order target: {target}")

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
        assert len(commands) >= 2, (
            f"Expected 2 or more words in build order command, got {raw_step}"
        )
        # supply at which to start
        try:
            supply = int(commands[0])
        except ValueError:
            logger.warning(
                f"""{raw_step} should begin with an integer supply count,
                found {commands[0]}, setting supply target to 0"""
            )
            supply = 0

        # this is the main command of a build order step (worker, gas, expand etc.)
        command: str = commands[1].upper()

        return supply, command

    def _get_main_scouting_points(
        self, order_target: BuildOrderTargetOptions, target_positions: list[Point2]
    ) -> list[Point2]:
        location: Point2 = self._get_target(order_target)
        # Using region perimeter to get some scout points
        # filter out areas by ramp and minerals as don't need to check there
        map_data: MapData = self.ai.mediator.get_map_data_object
        region: Region = map_data.in_region_p(location)
        perimeter: np.ndarray = region.perimeter
        ramp_point: Point2 = region.region_ramps[0].top_center.rounded
        ramp_point_array = np.array([ramp_point.x, ramp_point.y])
        distances = np.linalg.norm(perimeter - ramp_point_array, axis=1)
        filtered_points = perimeter[distances > 8.0]
        if len(filtered_points) == 0:
            return target_positions

        center = region.center
        angles = np.arctan2(
            filtered_points[:, 1] - center.y, filtered_points[:, 0] - center.x
        )
        ordered = filtered_points[np.argsort(angles)]

        if order_target == BuildOrderTargetOptions.ENEMY_SPAWN:
            ramp_point = region.region_ramps[0].top_center.rounded
            ramp_distances = np.linalg.norm(
                ordered - np.array([ramp_point.x, ramp_point.y]), axis=1
            )
            spawn_distances = np.linalg.norm(
                ordered - np.array([location.x, location.y]), axis=1
            )
            min_ramp = float(np.min(ramp_distances))
            # Prefer points that are closest to the ramp, then pick the side
            # closest to the enemy spawn.
            ramp_mask = ramp_distances <= (min_ramp + 0.5)
            if np.any(ramp_mask):
                candidate_indices = np.where(ramp_mask)[0]
                start_index = int(
                    candidate_indices[np.argmin(spawn_distances[candidate_indices])]
                )
            else:
                start_index = int(np.argmin(ramp_distances))
        else:
            start_distances = np.linalg.norm(
                ordered - np.array([location.x, location.y]), axis=1
            )
            start_index = int(np.argmin(start_distances))
        ordered = np.roll(ordered, -start_index, axis=0)

        min_spacing = 4.0
        last_point: np.ndarray | None = None
        for point in ordered:
            if last_point is None:
                _pos = Point2(cy_towards(point, location, 2.0))
                target_positions.append(_pos)
                last_point = point
                continue
            if np.linalg.norm(point - last_point) >= min_spacing:
                _pos = Point2(cy_towards(point, location, 2.0))
                target_positions.append(_pos)
                last_point = point

        return target_positions

    def _get_target(self, target: str | None) -> Point2:
        match target:
            case BuildOrderTargetOptions.ENEMY_FOURTH:
                return self.ai.mediator.get_enemy_expansions[2][0]
            case BuildOrderTargetOptions.ENEMY_NAT:
                return self.ai.mediator.get_enemy_nat
            case BuildOrderTargetOptions.ENEMY_NAT_HG_SPOT:
                return self.ai.mediator.get_ol_spot_near_enemy_nat
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

        num_same_steps_found: dict[UnitTypeId, int] = defaultdict(int)
        # pretend we already built things we spawn with
        # makes working this out easier
        num_same_steps_found[self.ai.base_townhall_type] = 1
        num_same_steps_found[UnitTypeId.OVERLORD] = 1
        num_same_steps_found[self.ai.worker_type] = 12

        for i, step in enumerate(build_order):
            command: AbilityId | UnitTypeId | UpgradeId = step.command
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
                    and step.target == UnitTypeId.NEXUS
                ):
                    logger.info(f"Removing {command} from build order")
                    indices_to_remove.append(i)
            elif isinstance(command, UnitTypeId):
                if command in ALL_STRUCTURES:
                    num_existing: int = len(
                        self.ai.mediator.get_own_structures_dict[command]
                    )
                    on_route: int = int(
                        self.ai.not_started_but_in_building_tracker(command)
                    )
                    total_present = num_existing + on_route
                else:
                    num_units: int = len(self.ai.mediator.get_own_army_dict[command])
                    pending: int = cy_unit_pending(self.ai, command)
                    total_present = num_units + pending

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
