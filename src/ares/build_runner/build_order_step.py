from typing import Callable, Union

from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId as UnitID
from sc2.ids.upgrade_id import UpgradeId


class BuildOrderStep:
    """Individual BuildOrderStep.

    Attributes
    ----------
    command : Union[AbilityId, UnitID, UpgradeId]
        What should happen in this step of the build order.

        Examples
        --------
        Extractor trick : AbilityId.CANCEL
        Train a Drone : UnitID.DRONE
        Research Zergling Speed: UpgradeId.ZERGLINGMOVEMENTSPEED

    command_started: bool
        Whether this step has started
    start_condition: Callable
        What should be checked to determine when this step should start
    end_condition: Callable
        What should be checked to determine when this step has been completed
    target: str
        Specifier in the case that additional information is needed to complete the step

    """

    def __init__(
        self,
        command: Union[AbilityId, UnitID, UpgradeId],
        start_condition: Callable,
        end_condition: Callable,
        target: str = "",
    ) -> None:
        self.command: Union[AbilityId, UnitID, UpgradeId] = command
        self.command_started: bool = False
        self.start_condition: Callable = start_condition
        self.end_condition: Callable = end_condition
        self.target: str = target
