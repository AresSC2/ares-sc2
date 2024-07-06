"""Handle manual tracking of abilities until python-sc2 PR #163 is merged.

"""
import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional, Union

from cython_extensions import cy_center, cy_distance_to_squared
from loguru import logger
from sc2.ids.unit_typeid import UnitTypeId as UnitID
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units

from ares.consts import DEBUG, ManagerName, ManagerRequestType, UnitRole
from ares.managers.manager import Manager
from ares.managers.manager_mediator import IManagerMediator, ManagerMediator

if TYPE_CHECKING:
    from ares import AresBot


@dataclass
class UnitSquad:
    """
    Create a new UnitSquad

    Attributes
    ----------
    main_squad : bool
        Is this the main squad of this type?
    squad_id : str
        Ideally this should be a unique identifier for this squad.
    squad_position : Point2
        The position where this group is situated.
    squad_units : list[Unit]
        List of units for this group. Ideally this should
        be updated with fresh Unit objects every step/frame.
    tags : set[int]
        Tags of all units that belong to this squad.

    """

    main_squad: bool
    squad_id: str
    squad_position: Point2
    squad_units: list[Unit]
    tags: set[int]

    def __repr__(self):
        return (
            f"Squad ID: {self.squad_id}, Position: {self.squad_position},"
            f"Num Units: {len(self.squad_units)}"
        )

    def set_main_squad(self, main_squad: bool) -> None:
        self.main_squad = main_squad

    def set_squad_position(self, position: Point2) -> None:
        self.squad_position = position

    def set_squad_units(self, units: list[Unit]) -> None:
        self.squad_units = units

    def set_squad_tags(self, tags: set[int]) -> None:
        self.tags = tags

    def remove_unit_tag(self, tag: int) -> None:
        if tag in self.tags:
            self.tags.remove(tag)


class SquadManager(Manager, IManagerMediator):
    """Manager to track UnitSquads

    Attributes
    ----------

    """

    SQUAD_OBJECT: str = "squad_object"
    TAGS: str = "tags"

    def __init__(
        self,
        ai: "AresBot",
        config: dict,
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
            ManagerRequestType.GET_POSITION_OF_MAIN_SQUAD: lambda kwargs: (
                self._get_position_of_main_squad(**kwargs)
            ),
            ManagerRequestType.GET_SQUADS: lambda kwargs: self._get_squads(**kwargs),
            ManagerRequestType.REMOVE_TAG_FROM_SQUADS: lambda kwargs: self.remove_tag(
                **kwargs
            ),
        }

        self._assigned_unit_tags: set[int] = set()
        # self._squads: dict[UnitRole, list[UnitSquad]] = defaultdict(list)
        # key -> UnitRole, value -> Dict[key -> squad_id, value -> tags, squad object]
        self._squads_dict: dict[UnitRole, dict[str, Any]] = {
            role: dict() for role in UnitRole
        }
        self._role_to_main_squad_pos: dict[UnitRole, Point2] = {
            role: ai.start_location for role in UnitRole
        }

    def manager_request(
        self,
        receiver: ManagerName,
        request: ManagerRequestType,
        reason: str = None,
        **kwargs,
    ) -> Any:
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

        """
        return self.manager_requests_dict[request](kwargs)

    async def update(self, _iteration: int) -> None:
        """
        When a user calls `self._get_squads()` squad calculation is done.


        Parameters
        ----------
        _iteration :
            The current game iteration

        Returns
        -------

        """
        if self.config[DEBUG]:
            for role, squad_dict in self._squads_dict.items():
                for squad_id, squad_info in squad_dict.items():
                    self.ai.draw_text_on_world(
                        squad_info["squad_object"].squad_position, f"{squad_id}"
                    )

    def remove_tag(self, tag: int) -> None:
        if tag in self._assigned_unit_tags:
            self._assigned_unit_tags.remove(tag)

            found_squad: bool = False
            squad_id_to_remove_from = ""
            role: UnitRole = UnitRole.ATTACKING
            for _role, squad_dict in self._squads_dict.items():
                for squad_id, squad_info in squad_dict.items():
                    if tag in squad_info[self.TAGS]:
                        squad_id_to_remove_from = squad_id
                        found_squad = True
                        role = _role
                        break
            if found_squad:
                self._remove_unit_tag(tag, role, squad_id_to_remove_from)

    def _get_squads(
        self,
        role: UnitRole,
        squad_radius: float = 6.0,
        unit_type: Optional[Union[UnitID, set[UnitID]]] = None,
    ) -> list[UnitSquad]:
        """
        The main entry point to this manager. Since we do not want
        to calculate squads unless user intends it.

        Parameters
        ----------
        role :
            The role in which we want to calculate squads for.
        squad_radius :
            Threshold that separates different squads.
        unit_type :
            Customize what unit_type should be managed.

        Returns
        -------
        list[UnitSquad] :
            A list of UnitSquad's for this role.

        """
        units: Units = self.ai.mediator.get_units_from_role(
            role=role, unit_type=unit_type
        )
        squads: list[UnitSquad] = self._squads_list_for_role(role)

        # we need to regenerate the squads with fresh unit collections etc
        self._regenerate_squads(role, squads, units)

        squads = self._squads_list_for_role(role)

        # need to merge squads, remove stray units from squads etc
        self._handle_existing_squads_assignment(role, squads, squad_radius)

        unassigned_units: list[Unit] = [
            u for u in units if u.tag not in self._assigned_unit_tags
        ]
        if unassigned_units:
            # now handle all units not currently assigned
            self._squad_assignment(
                role, unassigned_units, squad_radius, self._squads_list_for_role(role)
            )

        self._find_main_squad(role)

        # return the most up-to-date squads
        return self._squads_list_for_role(role)

    def _squads_list_for_role(self, role: UnitRole) -> list[UnitSquad]:
        """
        Get a list of all UnitSquads for this role

        Parameters
        ----------
        role

        Returns
        -------

        """
        return [
            squad_info[self.SQUAD_OBJECT]
            for squad_id, squad_info in self._squads_dict[role].items()
        ]

    def _squad_assignment(
        self,
        role: UnitRole,
        unassigned_units: list[Unit],
        squad_radius: float,
        squads: list[UnitSquad],
    ) -> None:
        """
        We have a unit not in any squad, work out what to do.

        Parameters
        ----------
        role
        unassigned_units
        squad_radius
        squads

        Returns
        -------

        """
        for unit in unassigned_units:
            tag: int = unit.tag
            # check if unit may join an existing squad
            squad_to_join: str = self._closest_squad_id(
                unit.position, squad_radius, squads
            )
            # found an existing squad to join
            if squad_to_join != "":
                self._squads_dict[role][squad_to_join][self.TAGS].add(tag)
                self._assigned_unit_tags.add(tag)
            # otherwise create a new squad containing just this unit
            else:
                self._create_squad(role, {tag})

    def _closest_squad_id(
        self,
        position: Point2,
        squad_radius: float,
        squads: list[UnitSquad],
        avoid_squad_id: str = "",
    ) -> str:
        """
        Get the closest squad to this `position`

        Parameters
        ----------
        position
        squad_radius
        squads
        avoid_squad_id

        Returns
        -------

        """
        if not squads:
            return ""

        closest_squad: UnitSquad = squads[0]
        min_distance: float = 999999.9
        for squad in squads:
            if squad.squad_id == avoid_squad_id:
                continue
            current_distance: float = cy_distance_to_squared(
                position, squad.squad_position
            )
            if current_distance < min_distance:
                closest_squad = squad
                min_distance = current_distance

        return closest_squad.squad_id if min_distance < squad_radius else ""

    def _create_squad(self, role: UnitRole, tags: set[int]) -> None:
        """
        Generate a brand-new squad

        Parameters
        ----------
        role
        tags

        Returns
        -------

        """
        squad_id: str = uuid.uuid4().hex
        squad_units: list[Unit] = [u for u in self.ai.units if u.tag in tags]
        if len(squad_units) == 0:
            return

        squad: UnitSquad = UnitSquad(
            main_squad=False,
            squad_id=squad_id,
            squad_position=Point2(cy_center(squad_units)),
            squad_units=squad_units,
            tags=tags,
        )
        self._squads_dict[role][squad_id] = {self.TAGS: tags, self.SQUAD_OBJECT: squad}
        for tag in tags:
            self._assigned_unit_tags.add(tag)

    def _regenerate_squads(
        self, role: UnitRole, squads: list[UnitSquad], units: Units
    ) -> None:
        """
        Regenerate info for recorded squads so information is up to
        date with current frame.

        Parameters
        ----------
        role
        squads
        units

        Returns
        -------

        """
        squads_to_remove: list[str] = []
        for squad in squads:
            tags: set[int] = self._squads_dict[role][squad.squad_id][self.TAGS]
            squad_units: list[Unit] = [u for u in units if u.tag in tags]

            # squads may contain no more units, remove it from records
            if not squad_units:
                squads_to_remove.append(squad.squad_id)
                for tag in tags:
                    self._assigned_unit_tags.remove(tag)
                continue

            self._squads_dict[role][squad.squad_id][self.SQUAD_OBJECT].set_squad_units(
                squad_units
            )
            self._squads_dict[role][squad.squad_id][
                self.SQUAD_OBJECT
            ].set_squad_position(Point2(cy_center(squad_units)))

        for squad_id in squads_to_remove:
            self._remove_squad(role, squad_id)

    def _remove_squad(self, role: UnitRole, squad_id: str) -> None:
        if squad_id in self._squads_dict[role]:
            for tag in self._squads_dict[role][squad_id][self.TAGS]:
                if tag in self._assigned_unit_tags:
                    self._assigned_unit_tags.remove(tag)
            del self._squads_dict[role][squad_id]

    def _handle_existing_squads_assignment(
        self, role: UnitRole, squads: list[UnitSquad], radius: float
    ) -> None:
        radius_squared: float = radius**2
        # Stray units get too far from squad -> Remove from current squad
        for squad in squads:
            in_range_tags: set[int] = {
                u.tag
                for u in squad.squad_units
                if cy_distance_to_squared(u.position, squad.squad_position)
                < radius_squared
            }
            for unit in squad.squad_units:
                if unit.tag not in in_range_tags:
                    self._remove_unit_tag(unit.tag, role, squad.squad_id)

        # Multiple squads overlapping -> Merge
        for squad in squads:
            if self._merge_with_closest_squad(
                squad.squad_position, role, radius, squad, squads
            ):
                # only merge one squad per frame, makes managing this somewhat easier
                break

    def _remove_unit_tag(self, tag: int, role: UnitRole, squad_id: str) -> None:
        """
        Remove a unit tag from any data structures
        """
        if squad_id not in self._squads_dict[role]:
            return

        if tag in self._squads_dict[role][squad_id][self.TAGS]:
            self._squads_dict[role][squad_id][self.TAGS].remove(tag)
            self._squads_dict[role][squad_id][self.SQUAD_OBJECT].remove_unit_tag(tag)
            if tag in self._assigned_unit_tags:
                self._assigned_unit_tags.remove(tag)

        # if this was the only unit in the squad, then remove the squad too
        if len(self._squads_dict[role][squad_id][self.TAGS]) == 0:
            self._remove_squad(role, squad_id)

    def _merge_with_closest_squad(
        self,
        pos: Point2,
        role: UnitRole,
        radius: float,
        squad_to_merge: UnitSquad,
        squads: list[UnitSquad],
    ) -> bool:
        """
        If we have two squads:
             - squad_to_merge should get removed
             - ensure unit tags are added to new squad
        Parameters
        ----------
        pos
        role
        radius
        squad_to_merge
        squads

        Returns
        -------
        bool :
            Indicating we merged squads.
        """
        closest_squad_id: str = self._closest_squad_id(
            pos, radius, squads, squad_to_merge.squad_id
        )
        if closest_squad_id != "":
            # remove this squad
            try:
                tags: list[int] = [u.tag for u in squad_to_merge.squad_units]
                self._remove_squad(role, squad_to_merge.squad_id)
                # add tags to new squad id
                self._squads_dict[role][closest_squad_id][self.TAGS].update(tags)
                for tag in tags:
                    self._assigned_unit_tags.add(tag)
                return True
            except KeyError:
                return False
        return False

    def _find_main_squad(self, role: UnitRole) -> None:
        """
        Find the main squad for this role

        Parameters
        ----------
        role

        Returns
        -------

        """
        squads: list[UnitSquad] = self._squads_list_for_role(role)
        if len(squads) == 0:
            return

        main_group_id = ""
        main_group_position: Point2 = squads[0].squad_position
        num_units_in_main_group: int = 0

        for squad in squads:
            amount: int = len(squad.squad_units)
            if amount >= num_units_in_main_group:
                main_group_id = squad.squad_id
                num_units_in_main_group = amount
                main_group_position = squad.squad_position

        for squad in squads:
            squad_id: str = squad.squad_id
            main_squad: bool = squad_id == main_group_id
            self._squads_dict[role][squad_id][self.SQUAD_OBJECT].set_main_squad(
                main_squad
            )
            if main_squad:
                self._role_to_main_squad_pos[role] = main_group_position

    def _get_position_of_main_squad(self, role: UnitRole) -> Point2:
        squads = self._squads_list_for_role(role)
        if len(squads) == 0:
            logger.warning(
                f"Attempting to find main squad for {role}, "
                f"but there are none assigned. Return value might be unexpected."
                f"Hint: Have you run `self.mediator.get_squads()` yet?"
            )
            return self._role_to_main_squad_pos[role]

        return self._role_to_main_squad_pos[role]
