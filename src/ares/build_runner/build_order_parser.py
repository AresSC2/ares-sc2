from dataclasses import dataclass
from typing import TYPE_CHECKING

from sc2.data import Race
from sc2.dicts.unit_trained_from import UNIT_TRAINED_FROM
from sc2.game_data import Cost
from sc2.ids.ability_id import AbilityId
from sc2.ids.buff_id import BuffId
from sc2.ids.unit_typeid import UnitTypeId as UnitID

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
    raw_build_order: List[str]
        The list of build order strings.
    build_order_step_dict: Optional[Dict]
        A dictionary of `BuildOrderStep` objects representing
        the recognized build order commands.

    Methods:
    --------
    parse() -> List[BuildOrderStep]:
        Parses the `raw_build_order` attribute into a list of `BuildOrderStep`.
    """

    ai: "AresBot"
    raw_build_order: list[str]
    build_order_step_dict: dict = None

    def __post_init__(self) -> None:
        """Initializes the `build_order_step_dict` attribute."""
        self.build_order_step_dict = self._generate_build_step_dict()

    def parse(self) -> list[BuildOrderStep]:
        """Parses the `raw_build_order` attribute into a list of `BuildOrderStep`.

        Returns:
        --------
        List[BuildOrderStep]
            The list of `BuildOrderStep` objects parsed from `raw_build_order`.
        """
        build_order: list[BuildOrderStep] = []
        for raw_step in self.raw_build_order:
            commands: list[str] = raw_step.split(" ")
            assert (
                len(commands) <= 3
            ), f"Build order strings should contain 3 or less words, got: {raw_step}"

            # this is the main command of a build order step (worker, gas, expand etc)
            command: str = commands[0].upper()

            # if a user passed a command matching a UnitTypeID enum key
            # then automatically handle that
            try:
                unit_id_command: UnitID = UnitID[command]
                if unit_id_command in ALL_STRUCTURES:
                    step: BuildOrderStep = self._generate_structure_build_step(
                        unit_id_command
                    )
                else:
                    step: BuildOrderStep = self._generate_unit_build_step(
                        unit_id_command
                    )
            except Exception:
                assert BuildOrderOptions.contains_key(
                    command
                ), f"Unrecognized build order command, got: {command}"
                step: BuildOrderStep = self.build_order_step_dict[
                    BuildOrderOptions[command]
                ]

            # check if user passed a target in, ie. ``expand @ natural``
            if len(commands) == 3:
                target = commands[-1].upper()
                try:
                    step.target = UnitID[target]
                except Exception:
                    assert BuildOrderTargetOptions.contains_key(
                        target
                    ), f"Unrecognized build option target, got: {target}"
                    step.target = BuildOrderTargetOptions[target]

            build_order.append(step)

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
            BuildOrderOptions.CHRONO: BuildOrderStep(
                command=AbilityId.EFFECT_CHRONOBOOST,
                start_condition=lambda: lambda: any(
                    [t.energy >= 50 for t in self.ai.townhalls]
                ),
                end_condition=lambda: any(
                    [
                        t.has_buff(BuffId.CHRONOBOOSTENERGYCOST)
                        for t in self.ai.townhalls
                    ]
                ),
            ),
            BuildOrderOptions.EXPAND: BuildOrderStep(
                command=self.ai.base_townhall_type,
                start_condition=lambda: self.ai.minerals >= min_minerals_for_expand,
                end_condition=lambda: self.ai.structures.filter(
                    lambda s: 0.00001 <= s.build_progress < 0.05
                    and s.type_id == self.ai.base_townhall_type
                ),
            ),
            BuildOrderOptions.GAS: BuildOrderStep(
                command=self.ai.gas_type,
                start_condition=lambda: self.ai.minerals >= 0
                if self.ai.race == Race.Zerg
                else 50,
                end_condition=lambda: self.ai.structures.filter(
                    lambda s: 0.00001 <= s.build_progress < 0.05
                    and s.type_id == self.ai.gas_type
                ),
            ),
            BuildOrderOptions.ORBITAL: BuildOrderStep(
                command=AbilityId.UPGRADETOORBITAL_ORBITALCOMMAND,
                start_condition=lambda: self.ai.minerals >= 150
                and self.ai.tech_requirement_progress(UnitID.ORBITALCOMMAND) == 1.0
                and self.ai.townhalls.filter(lambda th: th.is_ready and th.is_idle),
                end_condition=lambda: True,
            ),
            BuildOrderOptions.SUPPLY: BuildOrderStep(
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
            BuildOrderOptions.WORKER: BuildOrderStep(
                self.ai.worker_type,
                lambda: self._can_train_unit(self.ai.worker_type),
                # confident the start condition will auto make the end condition == True
                lambda: True,
            ),
        }

    def _generate_structure_build_step(self, structure_id: UnitID) -> BuildOrderStep:
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
        return BuildOrderStep(
            command=structure_id,
            start_condition=lambda: self.ai.minerals >= cost.minerals - 75,
            end_condition=lambda: self.ai.structures.filter(
                lambda s: 0.00001 <= s.build_progress < 0.05
                and s.type_id == structure_id
            ),
        )

    def _generate_unit_build_step(self, unit_id: UnitID) -> BuildOrderStep:
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
        return BuildOrderStep(
            command=unit_id,
            start_condition=lambda: self.ai.can_afford(unit_id)
            and self.ai.all_own_units.filter(
                lambda s: s.type_id in UNIT_TRAINED_FROM[unit_id]
                and s.build_progress == 1.0
                and s.is_idle
            ),
            # if start condition is True a train order will be issued
            # therefore it will automatically complete the step
            end_condition=lambda: True,
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
