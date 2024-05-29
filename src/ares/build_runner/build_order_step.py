from dataclasses import dataclass
from typing import Callable, Union

from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId as UnitID
from sc2.ids.upgrade_id import UpgradeId

from ares.consts import BuildOrderOptions


@dataclass
class BuildOrderStep:
    """Individual BuildOrderStep.

    Attributes
    ----------
    command : Union[AbilityId, UnitID, UpgradeId, BuildOrderOptions]
        What should happen in this step of the build order.

        Examples
        --------
        Extractor trick : AbilityId.CANCEL
        Train a Drone : UnitID.DRONE
        Research Zergling Speed: UpgradeId.ZERGLINGMOVEMENTSPEED
    start_condition: Callable
        What should be checked to determine when this step should start
    end_condition: Callable
        What should be checked to determine when this step has been completed
    command_started: bool
        Whether this step has started
    start_at_supply: int
        What supply should this step commence at
    target: str
        Specifier in the case that additional information is needed to complete the step

    """

    command: Union[AbilityId, UnitID, UpgradeId, BuildOrderOptions]
    start_condition: Callable
    end_condition: Callable
    command_started: bool = False
    start_at_supply: int = 0
    target: str = ""
