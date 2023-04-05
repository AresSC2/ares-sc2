from typing import TYPE_CHECKING, Optional, Union

from sc2.dicts.unit_trained_from import UNIT_TRAINED_FROM
from sc2.position import Point2
from sc2.ids.unit_typeid import UnitTypeId as UnitID
from sc2.unit import Unit

from ares.managers.build_runner import BuildOrderStep
from ares.managers.manager_mediator import ManagerMediator

if TYPE_CHECKING:
    from ares import AresBot
from ares.build_runner.build_order_parser import BuildOrderParser
from ares.consts import (
    BUILDS,
    OPENING_BUILD_ORDER,
    ALL_STRUCTURES,
    BuildOrderTargetOptions,
    GAS_BUILDINGS,
)
from loguru import logger


class BuildOrderRunner:
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
        build_order_parser: BuildOrderParser = BuildOrderParser(
            self.ai, config[BUILDS][chosen_opening][OPENING_BUILD_ORDER]
        )
        self.build_order: list[BuildOrderStep] = build_order_parser.parse()
        self.build_step: int = 0
        self.current_step_started: bool = False
        self._opening_build_completed: bool = False

    @property
    def build_completed(self) -> bool:
        return self._opening_build_completed

    async def run_build(self) -> None:
        if self.build_step >= len(self.build_order):
            self._opening_build_completed = True
            return

        await self.do_step(self.build_order[self.build_step])

    async def do_step(self, step: BuildOrderStep) -> None:
        if step.start_condition() and not self.current_step_started:
            command: UnitID = step.command
            if command in ALL_STRUCTURES:
                if pos := await self.get_position(command, step.target):
                    if worker := self.mediator.select_worker(
                        target_position=pos, force_close=True
                    ):
                        self.current_step_started = True
                        self.mediator.build_with_specific_worker(
                            worker=worker,
                            structure_type=command,
                            pos=pos,
                        )
            if type(command) == UnitID and command not in ALL_STRUCTURES:
                self.current_step_started = True
                self.ai.train(command)

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
