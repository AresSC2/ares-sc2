from abc import ABC, abstractmethod
from typing import Dict

from consts import BotMode
from custom_bot_ai import CustomBotAI
from managers.manager_mediator import ManagerMediator
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId as UnitID
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units


class BaseProduction(ABC):
    """
    Abstract class for Production facilities.
    """

    def __init__(
        self, ai: CustomBotAI, config: Dict, mediator: ManagerMediator
    ) -> None:
        """Set up the Production facility.

        Parameters
        ----------
        ai :
            Bot object that will be running the game
        config :
            Dictionary with the data from the configuration file
        mediator :
            ManagerMediator used for getting information from other managers.

        Returns
        -------

        """
        self.ai: CustomBotAI = ai
        self.config: Dict = config
        self.manager_mediator: ManagerMediator = mediator

    def count_unit(self, own_army: Dict, unit_type: UnitID) -> int:
        """Return the number of completed and pending units.

        Parameters
        ----------
        own_army :
            Dictionary of our own army.
        unit_type :
            Type of unit to count.

        Returns
        -------
        int :
            Total number of completed and pending units.

        """
        return len(own_army[unit_type]) + int(self.ai.already_pending(unit_type))

    @abstractmethod
    async def update(
        self,
        bot_mode: BotMode,
        building_loc: Point2,
        iteration: int,
    ) -> None:
        """Update the production facility.

        Parameters
        ----------
        bot_mode :
            Current BotMode.
        building_loc :
            Area to build structures near.
        iteration :
            The current game iteration.

        Returns
        -------

        """
        pass

    @staticmethod
    def cancel_structure(structure: Unit) -> None:
        """Cancel the given structure.

        Parameters
        ----------
        structure :
            The structure to cancel.

        Returns
        -------

        """
        if structure.build_progress < 1.0:
            structure(AbilityId.CANCEL_BUILDINPROGRESS)

    def find_area_in_front_of_base(
        self, townhall_location: Point2, distance_towards: int = 18
    ) -> Point2:
        """Find the area the other side of the minerals

        If no minerals present, then this will be towards map center.

        Parameters
        ----------
        townhall_location :
            Location of the townhall to find the area in front of.
        distance_towards :
            How far from the base the returned point should be.

        Returns
        -------
        Point2 :
            Center of the area in front of the base.

        """
        min_fields: Units = self.ai.mineral_field.filter(
            lambda mf: mf.distance_to(townhall_location) < 8
        )
        if min_fields and townhall_location != self.manager_mediator.get_own_nat:
            spine_area: Point2 = min_fields.center.towards(
                townhall_location, distance_towards
            )
        else:
            spine_area: Point2 = townhall_location.towards(
                self.ai.game_info.map_center, 6
            )

        return spine_area
