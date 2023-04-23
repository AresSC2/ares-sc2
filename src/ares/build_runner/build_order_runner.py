from typing import TYPE_CHECKING, Optional, Union

from sc2.data import Race
from sc2.ids.unit_typeid import UnitTypeId as UnitID
from sc2.position import Point2
from sc2.unit import Unit

from ares.managers.build_runner import BuildOrderStep
from ares.managers.manager_mediator import ManagerMediator

if TYPE_CHECKING:
    from ares import AresBot

from loguru import logger
from sc2.ids.ability_id import AbilityId

from ares.build_runner.build_order_parser import BuildOrderParser
from ares.consts import (
    ALL_STRUCTURES,
    BUILDS,
    GAS_BUILDINGS,
    OPENING_BUILD_ORDER,
    BuildOrderTargetOptions,
    UnitRole,
)


class BuildOrderRunner:
    """
    A class to run a build order for an AI.

    Attributes
    ----------
    ai : AresBot
        The AI that the build order is for.
    chosen_opening : str
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

    chosen_opening: str

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
        if BUILDS in self.config:
            build: list[str] = config[BUILDS][chosen_opening][OPENING_BUILD_ORDER]
        else:
            build: list[str] = []
        build_order_parser: BuildOrderParser = BuildOrderParser(self.ai, build)
        self.build_order: list[BuildOrderStep] = build_order_parser.parse()
        self.build_step: int = 0
        self.current_step_started: bool = False
        self._opening_build_completed: bool = False
        self.current_build_position: Point2 = self.ai.start_location
        self.assigned_persistent_worker: bool = False

    @property
    def build_completed(self) -> bool:
        """
        Returns
        -------
        bool
            True if the opening build is completed, False otherwise.
        """
        return self._opening_build_completed

    async def run_build(self) -> None:
        """
        Runs the build order.
        """
        self._assign_persistent_worker()
        if self.build_step >= len(self.build_order):
            self.mediator.switch_roles(
                from_role=UnitRole.PERSISTENT_BUILDER, to_role=UnitRole.GATHERING
            )
            self._opening_build_completed = True
            return

        await self.do_step(self.build_order[self.build_step])

    async def do_step(self, step: BuildOrderStep) -> None:
        """
        Runs a specific build order step.

        Parameters
        ----------
        step : BuildOrderStep
            The build order step to run.
        """
        if next_building_position := await self.get_position(step.command, step.target):
            self.current_build_position = next_building_position

        if step.start_condition() and not self.current_step_started:
            command: UnitID = step.command
            if command in ALL_STRUCTURES:
                if worker := self.mediator.select_worker(
                    target_position=self.current_build_position,
                    force_close=True,
                    select_persistent_builder=command != UnitID.REFINERY,
                    only_select_persistent_builder=command == UnitID.BARRACKS
                    and self.ai.time < 60.0,
                ):
                    self.current_step_started = True
                    self.mediator.build_with_specific_worker(
                        worker=worker,
                        structure_type=command,
                        pos=self.current_build_position,
                        assign_role=worker.tag
                        in self.mediator.get_unit_role_dict[UnitRole.GATHERING],
                    )
            if type(command) == UnitID and command not in ALL_STRUCTURES:
                self.current_step_started = True
                self.ai.train(command)

            elif command == AbilityId.EFFECT_CHRONOBOOST:
                if chrono_target := self.get_structure(step.target):
                    if available_nexuses := [
                        th for th in self.ai.townhalls if th.energy >= 50
                    ]:
                        available_nexuses[0](
                            AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, chrono_target
                        )
                        self.current_step_started = True

        # current step started and end condition hasn't yet activated
        if not step.end_condition() and self.current_step_started:
            pass

        if step.end_condition() and self.current_step_started:
            logger.info(
                f"{self.ai.supply_used} {self.ai.time_formatted} {step.command.name}"
            )
            self.build_step += 1
            self.current_step_started = False

    async def get_position(
        self, structure_type: UnitID, target: Optional[str]
    ) -> Union[Point2, Unit]:
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
            return self.ai.vespene_geyser.closest_to(self.ai.start_location)
        if target == BuildOrderTargetOptions.RAMP:
            if structure_type == self.ai.supply_type:
                return list(self.ai.main_base_ramp.corner_depots)[0]

        if structure_type == self.ai.base_townhall_type:
            return await self.ai.get_next_expansion()

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
        if type(target) == UnitID:
            if valid_structures := self.ai.structures.filter(
                lambda s: s.build_progress == 1.0 and s.type_id == target
            ):
                return valid_structures.first

    def _assign_persistent_worker(self) -> None:
        """Assign a worker that does not get assigned back to gathering."""
        if (
            # terran specific for now
            self.ai.race == Race.Terran
            and self.ai.time > 10
            and not self.assigned_persistent_worker
        ):
            if worker := self.mediator.select_worker(
                target_position=self.ai.start_location
            ):
                self.mediator.assign_role(
                    tag=worker.tag, role=UnitRole.PERSISTENT_BUILDER
                )
                self.assigned_persistent_worker = True
                # Move the worker in general position towards building area
                # TODO: Once building placement is finished, move to building position
                #   Which will always be a supply building
                worker.move(
                    self.ai.start_location.towards(
                        self.ai.main_base_ramp.top_center, 7.0
                    )
                )
