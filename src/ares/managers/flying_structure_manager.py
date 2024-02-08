"""Handle manual tracking of abilities until python-sc2 PR #163 is merged.

"""
from typing import TYPE_CHECKING, Dict, Optional

from cython_extensions import cy_distance_to_squared
from sc2.ids.ability_id import AbilityId
from sc2.position import Point2
from sc2.unit import Unit

from ares.consts import ManagerName, ManagerRequestType
from ares.managers.manager import Manager
from ares.managers.manager_mediator import IManagerMediator, ManagerMediator

if TYPE_CHECKING:
    from ares import AresBot


class FlyingStructureManager(Manager, IManagerMediator):
    """Manager to track flying structures

    Attributes
    ----------

    """

    def __init__(
        self,
        ai: "AresBot",
        config: Dict,
        mediator: ManagerMediator,
    ) -> None:
        """Set up the manager.

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
        super().__init__(ai, config, mediator)
        self.manager_requests_dict = {
            ManagerRequestType.GET_FLYING_STRUCTURE_TRACKER: lambda kwargs: (
                self.flying_structure_tracker
            ),
            ManagerRequestType.MOVE_STRUCTURE: lambda kwargs: (
                self.move_structure(**kwargs)
            ),
        }
        # key -> structure_tag, value -> {destination, should_land}
        self._flying_structure_tracker: dict[int, dict] = dict()

    @property
    def flying_structure_tracker(self):
        return self._flying_structure_tracker

    def manager_request(
        self,
        receiver: ManagerName,
        request: ManagerRequestType,
        reason: str = None,
        **kwargs
    ) -> Optional[Dict]:
        """Fetch information from this Manager so another Manager can use it.

        Parameters
        ----------
        receiver :
            This Manager.
        request :
            What kind of request is being made
        reason :
            Why the reason is being made
        kwargs :
            Additional keyword args if needed for the specific request, as determined
            by the function signature (if appropriate)

        Returns
        -------
        Optional[Dict] :
            Either one of the ability dictionaries is being returned or a function that
            returns None was called from a different manager (please don't do that).

        """
        return self.manager_requests_dict[request](kwargs)

    async def update(self, _iteration: int) -> None:
        """Not used by this manager.

        Manager is an abstract class and must have an ``update`` method.

        Parameters
        ----------
        _iteration :
            The current game iteration

        Returns
        -------

        """
        self._handle_flying_structures()

    def move_structure(
        self, structure: Unit, target: Point2, should_land: bool = True
    ) -> None:
        """
        Request a structure to move.
        If structure is already present in tracking, override command.


        Parameters
        ----------
        structure
        target
        should_land

        Returns
        -------

        """
        self._flying_structure_tracker[structure.tag] = {
            "destination": target,
            "should_land": should_land,
        }

    def _handle_flying_structures(self) -> None:
        tags_to_remove: list[int] = []
        for structure_tag, info in self._flying_structure_tracker.items():
            target: Point2 = info["destination"]
            should_land: bool = info["should_land"]
            structure: Optional[Unit] = self.ai.unit_tag_dict.get(structure_tag, None)
            if not structure:
                tags_to_remove.append(structure_tag)
                continue

            dist_to_target: float = cy_distance_to_squared(structure.position, target)
            if not structure.is_flying:
                if structure.position == target:
                    tags_to_remove.append(structure_tag)
                    continue

                structure(AbilityId.CANCEL_QUEUE5)
                structure(AbilityId.LIFT, queue=True)
            else:
                if dist_to_target < 30.25:  # 5.5
                    if should_land:
                        structure(AbilityId.LAND, target)
                else:
                    structure.move(target)

        for tag in tags_to_remove:
            self._flying_structure_tracker.pop(tag)
