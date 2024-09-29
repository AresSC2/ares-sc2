from typing import TYPE_CHECKING, Optional, Union

from cython_extensions import cy_distance_to_squared, cy_towards
from sc2.data import Race
from sc2.ids.unit_typeid import UnitTypeId as UnitID
from sc2.ids.upgrade_id import UpgradeId
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units

from ares.behaviors.macro import AutoSupply, SpawnController
from ares.build_runner.build_order_step import BuildOrderStep
from ares.managers.manager_mediator import ManagerMediator

if TYPE_CHECKING:
    from ares import AresBot

from loguru import logger
from sc2.ids.ability_id import AbilityId

from ares.build_runner.build_order_parser import BuildOrderParser
from ares.consts import (
    ADD_ONS,
    ALL_STRUCTURES,
    BUILDS,
    GAS_BUILDINGS,
    GATEWAY_UNITS,
    OPENING_BUILD_ORDER,
    TARGET,
    BuildOrderOptions,
    BuildOrderTargetOptions,
    UnitRole,
)
from ares.dicts.structure_to_building_size import STRUCTURE_TO_BUILDING_SIZE


class BuildOrderRunner:
    """
    A class to run a build order for an AI.

    Attributes
    ----------
    ai : AresBot
        The AI that the build order is for.
    _chosen_opening : str
        The name of the opening being used for the build order.
    config : dict
        The configuration dictionary for the AI.
    mediator : ManagerMediator
        The ManagerMediator object used for communicating with managers.
    build_order : list[BuildOrderStep]
        The build order list.
    build_step : int
        The current build order step index.
    current_step_started : bool
        True if the current build order step has started, False otherwise.
    _opening_build_completed : bool
        True if the opening build is completed, False otherwise.

    Methods
    -------
    run_build()
        Runs the build order.
    do_step(step: BuildOrderStep)
        Runs a specific build order step.
    """

    AUTO_SUPPLY_AT_SUPPLY: str = "AutoSupplyAtSupply"
    CONSTANT_WORKER_PRODUCTION_TILL: str = "ConstantWorkerProductionTill"
    PERSISTENT_WORKER: str = "PersistentWorker"
    REQUIRES_TOWNHALL_COMMANDS: set = {
        AbilityId.UPGRADETOORBITAL_ORBITALCOMMAND,
        AbilityId.UPGRADETOPLANETARYFORTRESS_PLANETARYFORTRESS,
    }
    SCOUTING_COMMANDS: set[BuildOrderOptions] = {
        BuildOrderOptions.OVERLORD_SCOUT,
        BuildOrderOptions.WORKER_SCOUT,
    }

    def __init__(
        self,
        ai: "AresBot",
        chosen_opening: str,
        config: dict,
        mediator: ManagerMediator,
    ) -> None:
        self.ai = ai
        self.config: dict = config
        self.mediator: ManagerMediator = mediator
        self.auto_supply_at_supply: int = 200
        self.constant_worker_production_till: int = 0
        self.persistent_worker: bool = True

        self.build_order: list[BuildOrderStep] = []
        self._build_order_parser: BuildOrderParser = BuildOrderParser(self.ai)
        self._chosen_opening: str = chosen_opening
        self.configure_opening_from_yml_file(config, chosen_opening)

        self.build_step: int = 0
        self.current_step_started: bool = False
        self.current_step_complete: bool = False
        self._opening_build_completed: bool = False
        self.current_build_position: Point2 = self.ai.start_location
        self.assigned_persistent_worker: bool = False

        self._temporary_build_step: int = -1

    def set_build_completed(self) -> None:
        logger.info("Build order completed")
        self.mediator.switch_roles(
            from_role=UnitRole.PERSISTENT_BUILDER, to_role=UnitRole.GATHERING
        )
        self._opening_build_completed = True

    def configure_opening_from_yml_file(
        self, config: dict, opening_name: str, remove_completed: bool = False
    ) -> None:
        if BUILDS in self.config:
            assert isinstance(
                config[BUILDS], dict
            ), "Opening builds are not configured correctly in the yml file"

            assert opening_name in config[BUILDS].keys(), (
                f"Trying to parse an opening called {opening_name} but "
                f"I can't find it. Spelling perhaps?"
            )

            build: list[str] = config[BUILDS][opening_name][OPENING_BUILD_ORDER]
            logger.info(
                f"{self.ai.time_formatted}: Running build from yml file: {opening_name}"
            )
            if self.AUTO_SUPPLY_AT_SUPPLY in config[BUILDS][opening_name]:
                try:
                    self.auto_supply_at_supply = int(
                        config[BUILDS][opening_name][self.AUTO_SUPPLY_AT_SUPPLY]
                    )
                except ValueError as e:
                    logger.warning(f"Error: {e}")
            if self.CONSTANT_WORKER_PRODUCTION_TILL in config[BUILDS][opening_name]:
                try:
                    self.constant_worker_production_till = int(
                        config[BUILDS][opening_name][
                            self.CONSTANT_WORKER_PRODUCTION_TILL
                        ]
                    )
                except ValueError as e:
                    logger.warning(f"Error: {e}")
            if self.PERSISTENT_WORKER in config[BUILDS][opening_name]:
                self.persistent_worker = config[BUILDS][opening_name][
                    self.PERSISTENT_WORKER
                ]

            self.build_step: int = 0
            self.current_step_started: bool = False
            self.current_step_complete: bool = False
            self.current_build_position: Point2 = self.ai.start_location
            self.assigned_persistent_worker: bool = False
            self._temporary_build_step: int = -1

            self.build_order = self._build_order_parser.parse(build, remove_completed)

    def set_step_complete(self, value: UnitID) -> None:
        if (
            self.build_step < len(self.build_order)
            and value == self.build_order[self.build_step].command
            and self.current_step_started
        ):
            self.current_step_complete = True

    def set_step_started(self, value: bool, command) -> None:
        if command == self.build_order[self.build_step].command:
            self.current_step_started = value

    def switch_opening(self, opening_name: str, remove_completed: bool = True) -> None:
        if self._chosen_opening != opening_name:
            self._chosen_opening = opening_name
            self.configure_opening_from_yml_file(
                self.config, opening_name, remove_completed=remove_completed
            )

    @property
    def build_completed(self) -> bool:
        """
        Returns
        -------
        bool
            True if the opening build is completed, False otherwise.
        """
        return self._opening_build_completed

    @property
    def chosen_opening(self) -> str:
        """
        Returns
        -------
        str
            Get the name of the opening (same name as declared in builds.yml file).
        """
        return self._chosen_opening

    @property
    def look_ahead(self) -> bool:
        """
        Can look ahead in the build order?
        """
        return self.ai.minerals > 470 and self._temporary_build_step == -1

    async def run_build(self) -> None:
        """
        Runs the build order.
        """
        if self.persistent_worker:
            self._assign_persistent_worker()
        if len(self.build_order) > 0:
            if self._temporary_build_step != -1:
                await self.do_step(self.build_order[self._temporary_build_step])
            else:
                await self.do_step(self.build_order[self.build_step])

            # if we are a bit stuck on current step, we can look ahead
            # and attempt to complete a future step
            if self.look_ahead:
                index: int = 0
                for i, step in enumerate(self.build_order[self.build_step :]):
                    if index == 0:
                        continue
                    index += 1
                    if step.start_condition():
                        self.current_step_started = False
                        self._temporary_build_step = i
                        break

        if not self.build_completed and self.build_step >= len(self.build_order):
            self.set_build_completed()
            logger.info("Build order completed")
            return

        if self.ai.supply_workers < self.constant_worker_production_till:
            self._produce_workers()

        if self.ai.supply_used >= self.auto_supply_at_supply:
            AutoSupply(self.ai.start_location).execute(
                self.ai, self.config, self.mediator
            )

    async def do_step(self, step: BuildOrderStep) -> None:
        """
        Runs a specific build order step.

        Parameters
        ----------
        step : BuildOrderStep
            The build order step to run.
        """
        if (
            step.command in GATEWAY_UNITS
            and UpgradeId.WARPGATERESEARCH in self.ai.state.upgrades
            and [
                g
                for g in self.mediator.get_own_structures_dict[UnitID.GATEWAY]
                if g.is_ready and g.is_idle
            ]
        ):
            return

        start_at_supply: int = step.start_at_supply
        start_condition_triggered: bool = step.start_condition()
        # start condition is active for a structure? reduce the supply threshold
        # this allows a worker to be sent earlier
        if (
            self.ai.race == Race.Protoss
            and start_condition_triggered
            and step.command in ALL_STRUCTURES
            and step.command != UnitID.PYLON
        ):
            start_at_supply -= 1
        if (
            start_condition_triggered
            and not self.current_step_started
            and self.ai.supply_used >= start_at_supply
        ):
            command: UnitID = step.command
            if command in ADD_ONS:
                self.current_step_started = True
            elif command in ALL_STRUCTURES:
                persistent_workers: Units = self.mediator.get_units_from_role(
                    role=UnitRole.PERSISTENT_BUILDER
                )
                building_tracker: dict = self.mediator.get_building_tracker_dict
                persistent_worker_available: bool = False
                if self.persistent_worker:
                    for worker in persistent_workers:
                        if self.ai.race == Race.Protoss:
                            persistent_worker_available = True
                            break
                        if worker.tag in building_tracker:
                            target: Point2 = building_tracker[worker.tag][TARGET]
                            if [
                                s
                                for s in self.ai.structures
                                if cy_distance_to_squared(s.position, target) < 6
                                and s.build_progress > 0.95
                            ]:
                                persistent_worker_available = True
                if worker := self.mediator.select_worker(
                    target_position=self.current_build_position,
                    force_close=True,
                    select_persistent_builder=command != UnitID.REFINERY,
                    only_select_persistent_builder=persistent_worker_available,
                ):
                    if next_building_position := await self.get_position(
                        step.command, step.target
                    ):
                        self.current_build_position = next_building_position
                        if self.mediator.build_with_specific_worker(
                            worker=worker,
                            structure_type=command,
                            pos=self.current_build_position,
                            assign_role=worker.tag
                            in self.mediator.get_unit_role_dict[UnitRole.GATHERING],
                        ):
                            self.current_step_started = True

            elif isinstance(command, UnitID) and command not in ALL_STRUCTURES:
                army_comp: dict = {command: {"proportion": 1.0, "priority": 0}}
                spawn_target: Point2 = self._get_target(step.target)
                SpawnController(
                    army_comp, freeflow_mode=True, maximum=1, spawn_target=spawn_target
                ).execute(self.ai, self.config, self.mediator)
                if (
                    UpgradeId.WARPGATERESEARCH in self.ai.state.upgrades
                    and command in GATEWAY_UNITS
                ):
                    # main.on_unit_created will set self.current_step_started = True
                    pass
                else:
                    self.current_step_started = True

            elif isinstance(command, UpgradeId):
                self.current_step_started = True
                self.ai.research(command)

            elif command == AbilityId.EFFECT_CHRONOBOOST:
                if chrono_target := self.get_structure(step.target):
                    if available_nexuses := [
                        th
                        for th in self.ai.townhalls
                        if th.energy >= 50 and th.is_ready
                    ]:
                        available_nexuses[0](
                            AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, chrono_target
                        )
                        self.current_step_started = True

            elif command == AbilityId.UPGRADETOORBITAL_ORBITALCOMMAND:
                if available_ccs := [
                    th
                    for th in self.ai.townhalls
                    if th.is_idle and th.is_ready and th.type_id == UnitID.COMMANDCENTER
                ]:
                    available_ccs[0](AbilityId.UPGRADETOORBITAL_ORBITALCOMMAND)
                    self.current_step_started = True

            elif command == BuildOrderOptions.WORKER_SCOUT:
                if worker := self.mediator.select_worker(
                    target_position=self.ai.start_location
                ):
                    worker.return_resource()
                    for target in step.target:
                        worker.move(target, queue=True)
                    self.mediator.assign_role(
                        tag=worker.tag, role=UnitRole.BUILD_RUNNER_SCOUT
                    )
                    self.current_step_started = True
            elif command == BuildOrderOptions.OVERLORD_SCOUT:
                unit_role_dict: dict[
                    UnitRole, set[int]
                ] = self.mediator.get_unit_role_dict
                if overlords := [
                    ol
                    for ol in self.mediator.get_own_army_dict[UnitID.OVERLORD]
                    if ol.tag not in unit_role_dict[UnitRole.BUILD_RUNNER_SCOUT]
                ]:
                    overlord: Unit = overlords[0]
                    for i, target in enumerate(step.target):
                        overlord.move(target, queue=i != 0)
                    self.mediator.assign_role(
                        tag=overlord.tag, role=UnitRole.BUILD_RUNNER_SCOUT
                    )
                    self.current_step_started = True

        if self.current_step_started:
            if not self.current_step_complete:
                self.current_step_complete = step.end_condition()
            # end condition hasn't yet activated
            if not self.current_step_complete:
                command: Union[UnitID, UpgradeId] = step.command
                if command in ADD_ONS and self.ai.can_afford(command):
                    if base_structures := [
                        s
                        for s in self.ai.structures
                        if s.is_ready and s.is_idle and s.type_id == ADD_ONS[command]
                    ]:
                        base_structures[0].build(command)
                # should have already started upgraded when step started,
                # backup here just in case
                elif isinstance(command, UpgradeId):
                    self.ai.research(command)
                elif command == UnitID.ARCHON:
                    army_comp: dict = {command: {"proportion": 1.0, "priority": 0}}
                    SpawnController(army_comp, freeflow_mode=True, maximum=1).execute(
                        self.ai, self.config, self.mediator
                    )

            # end condition active, complete step
            else:
                time: str = self.ai.time_formatted
                logger.info(f"{self.ai.supply_used} {time} {step.command.name}")
                if self._temporary_build_step != -1:
                    self.build_order.remove(
                        self.build_order[self._temporary_build_step]
                    )
                    self._temporary_build_step = -1
                else:
                    self.build_step += 1

                self.current_step_started = False
                self.current_step_complete = False
                if step.command == UnitID.PYLON:
                    self.mediator.switch_roles(
                        from_role=UnitRole.PERSISTENT_BUILDER,
                        to_role=UnitRole.GATHERING,
                    )

    async def get_position(
        self, structure_type: UnitID, target: Optional[str]
    ) -> Union[Point2, Unit, None]:
        """Convert a position command from the build order to an actual location.
        Examples
        --------
        "expand @ nat" :
            ``if structure_type == self.ai.base_townhall_type and target == "NAT":``
                ``return self.manager_mediator.get_own_nat``
        Parameters
        ----------
        structure_type :
            The type of structure to build
        target :
            Where the structure should be built
        Returns
        -------
        Point2, Unit :
            The actual game location where the structure should be built
            Or vespene geyser Unit for gas buildings
        """
        if structure_type in GAS_BUILDINGS:
            existing_gas_buildings: Units = self.ai.all_units(GAS_BUILDINGS)
            if available_geysers := self.ai.vespene_geyser.filter(
                lambda g: not existing_gas_buildings.closer_than(5.0, g)
                and self.ai.townhalls.closer_than(12.0, g)
            ):
                return available_geysers.closest_to(self.ai.start_location)
        elif structure_type == self.ai.base_townhall_type:
            return await self.ai.get_next_expansion()
        elif self.ai.race != Race.Zerg:
            within_psionic_matrix: bool = (
                self.ai.race == Race.Protoss
                and structure_type in STRUCTURE_TO_BUILDING_SIZE
                and structure_type != UnitID.PYLON
            )
            at_wall: bool = target == BuildOrderTargetOptions.RAMP
            close_enemy_to_ramp: list[Unit] = [
                e
                for e in self.ai.enemy_units
                if cy_distance_to_squared(e.position, self.ai.main_base_ramp.top_center)
                < 100.0
            ]
            if len(close_enemy_to_ramp) > 0:
                at_wall = False
            if target == BuildOrderTargetOptions.RAMP:
                base_location = self.ai.start_location
            else:
                base_location = self._get_target(target)
            if pos := self.mediator.request_building_placement(
                base_location=base_location,
                structure_type=structure_type,
                wall=at_wall,
                within_psionic_matrix=within_psionic_matrix,
                pylon_build_progress=0.5,
            ):
                return pos
        else:
            if target == BuildOrderTargetOptions.RAMP:
                if structure_type == self.ai.supply_type:
                    return list(self.ai.main_base_ramp.corner_depots)[0]

            return await self.ai.find_placement(
                structure_type,
                self.ai.start_location.towards(self.ai.game_info.map_center, 8.0),
                30,
            )

    def get_structure(self, target: str) -> Optional[Unit]:
        """Get the first structure matching the specified type.
        Parameters
        ----------
        target :
            Type of building to be returned.
        Returns
        -------
        Optional[Unit] :
            Unit of the structure type if found.
        """
        # this block is currently for chrono
        if isinstance(target, UnitID):
            if valid_structures := self.ai.structures.filter(
                lambda s: s.build_progress == 1.0 and s.type_id == target
            ):
                return valid_structures.first

    def _assign_persistent_worker(self) -> None:
        """Assign a worker that does not get assigned back to gathering."""
        if self.ai.race != Race.Zerg and not self.assigned_persistent_worker:
            pos, time = self._get_position_and_supply_of_first_supply()
            if self.ai.time >= time:
                if worker := self.mediator.select_worker(
                    target_position=self.ai.start_location
                ):
                    self.mediator.assign_role(
                        tag=worker.tag, role=UnitRole.PERSISTENT_BUILDER
                    )
                    self.assigned_persistent_worker = True
                    worker.move(pos)

    def _produce_workers(self):
        if (
            self.ai.supply_left > 0
            and not self.build_completed
            and self.ai.townhalls.idle
            and self.ai.can_afford(self.ai.worker_type)
            # check if current command requires an idle townhall
            and (
                self.build_order[self.build_step].command
                not in self.REQUIRES_TOWNHALL_COMMANDS
                or self.ai.supply_used
                < self.build_order[self.build_step].start_at_supply
            )
        ):
            self.ai.train(self.ai.worker_type)

    def _get_target(self, target: Optional[str]) -> Point2:
        match target:
            case BuildOrderTargetOptions.ENEMY_FOURTH:
                return self.mediator.get_enemy_expansions[2][0]
            case BuildOrderTargetOptions.ENEMY_NAT:
                return self.mediator.get_enemy_nat
            case BuildOrderTargetOptions.ENEMY_NAT_HG_SPOT:
                return self.mediator.get_closest_overlord_spot(
                    from_pos=Point2(
                        cy_towards(
                            self.mediator.get_enemy_nat,
                            self.ai.game_info.map_center,
                            10.0,
                        )
                    )
                )
            case BuildOrderTargetOptions.ENEMY_NAT_VISION:
                return Point2(
                    cy_towards(
                        self.mediator.get_enemy_nat,
                        self.ai.game_info.map_center,
                        10.0,
                    )
                )
            case BuildOrderTargetOptions.ENEMY_RAMP:
                return self.mediator.get_enemy_ramp.top_center
            case BuildOrderTargetOptions.ENEMY_SPAWN:
                return self.ai.enemy_start_locations[0]
            case BuildOrderTargetOptions.ENEMY_THIRD:
                return self.mediator.get_enemy_expansions[1][0]
            case BuildOrderTargetOptions.FIFTH:
                return self.mediator.get_own_expansions[3][0]
            case BuildOrderTargetOptions.FOURTH:
                return self.mediator.get_own_expansions[2][0]
            case BuildOrderTargetOptions.MAP_CENTER:
                return self.ai.game_info.map_center
            case BuildOrderTargetOptions.NAT:
                return self.mediator.get_own_nat
            case BuildOrderTargetOptions.RAMP:
                return self.ai.main_base_ramp.top_center
            case BuildOrderTargetOptions.SIXTH:
                return self.mediator.get_own_expansions[4][0]
            case BuildOrderTargetOptions.SPAWN:
                return self.ai.start_location
            case BuildOrderTargetOptions.THIRD:
                return self.mediator.get_own_expansions[1][0]
        return self.ai.start_location

    def _get_position_and_supply_of_first_supply(self) -> tuple[Point2, float]:
        """
        Iterate through the build order, and work out
        where first supply structure will go.
        Used to send worker early

        Returns
        -------

        """
        for step in self.build_order:
            if step.command in {UnitID.SUPPLYDEPOT, UnitID.PYLON}:
                target: Point2 = self._get_target(step.target)
                time = (
                    3.0
                    if step.start_at_supply <= 13 or target == self.mediator.get_own_nat
                    else 9.0
                )
                if self.ai.time < time:
                    return self.ai.start_location, 999.9

                return (
                    self.mediator.request_building_placement(
                        base_location=target,
                        structure_type=self.ai.supply_type,
                        reserve_placement=False,
                    ),
                    time,
                )

        return self.ai.start_location, 999.9
