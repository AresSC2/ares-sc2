"""Manage assigning/removing of roles and getting units by role.

"""
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set, Union

from sc2.ids.unit_typeid import UnitTypeId as UnitID
from sc2.unit import Unit
from sc2.units import Units

from ares.consts import (
    UNIT_TYPES_WITH_NO_ROLE,
    ManagerName,
    ManagerRequestType,
    UnitRole,
)
from ares.managers.manager import Manager
from ares.managers.manager_mediator import IManagerMediator, ManagerMediator

if TYPE_CHECKING:
    from ares import AresBot


class UnitRoleManager(Manager, IManagerMediator):
    """Assign and remove roles as well as organize units by role.

    Other Managers should call this Manager's functions rather than assigning roles
    themselves.
    """

    LOCUSTS: Set[UnitID] = {UnitID.LOCUSTMP, UnitID.LOCUSTMPFLYING}
    SQUAD_ROLES: Set[UnitRole] = {UnitRole.ATTACKING}
    ZERG_STATIC_DEFENCE: Set[UnitID] = {UnitID.SPINECRAWLER, UnitID.SPORECRAWLER}

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
        super(UnitRoleManager, self).__init__(ai, config, mediator)
        self.unit_role_dict: Dict[str, Set[int]] = {
            role.name: set() for role in UnitRole
        }
        self.tag_to_role_dict: Dict[int, str] = {}
        self.manager_requests_dict = {
            ManagerRequestType.ASSIGN_ROLE: lambda kwargs: self.assign_role(**kwargs),
            ManagerRequestType.BATCH_ASSIGN_ROLE: lambda kwargs: self.batch_assign_role(
                **kwargs
            ),
            ManagerRequestType.CLEAR_ROLE: lambda kwargs: self.clear_role(**kwargs),
            ManagerRequestType.GET_ALL_FROM_ROLES_EXCEPT: lambda kwargs: (
                self.get_all_from_roles_except(**kwargs)
            ),
            ManagerRequestType.GET_UNIT_ROLE_DICT: lambda kwargs: self.unit_role_dict,
            ManagerRequestType.GET_UNITS_FROM_ROLE: lambda kwargs: (
                self.get_units_from_role(**kwargs)
            ),
            ManagerRequestType.GET_UNITS_FROM_ROLES: lambda kwargs: (
                self.get_units_from_roles(**kwargs)
            ),
            ManagerRequestType.SWITCH_ROLES: lambda kwargs: self.switch_roles(**kwargs),
        }
        self.all_assigned_tags: Set[int] = set()

    def manager_request(
        self,
        receiver: ManagerName,
        request: ManagerRequestType,
        reason: str = None,
        **kwargs,
    ) -> Any:
        """Enables ManagerRequests to this Manager.

        Parameters
        ----------
        receiver :
            The Manager the request is being sent to.
        request :
            The Manager that made the request
        reason :
            Why the Manager has made the request
        kwargs :
            If the ManagerRequest is calling a function, that function's keyword
            arguments go here.

        Returns
        -------
        Any

        """
        return self.manager_requests_dict[request](kwargs)

    async def update(self, iteration: int) -> None:
        """Update Overseer role in realtime.

        Notes
        -----
        This is just a workaround for a realtime bug and is generally unused.

        Parameters
        ----------
        iteration :
            The game iteration.

        Returns
        -------

        """
        # This is a workaround to realtime overseers keeping their SCOUTING role from
        # overlord
        # TODO: Fix the root cause of this bug and remove this `if realtime` block
        # TODO: This was an Eris fix, commented out for now to be investigated later
        # if self.ai.realtime and iteration % 8 == 0:
        #     overseers: Units = self.manager_mediator.get_units_from_role(
        #         role=UnitRole.SCOUTING, unit_type=UnitID.OVERSEER
        #     )
        #     # Bots should assign appropriately once overseers have defending role
        #     for overseer in overseers:
        #         self.assign_role(overseer.tag, UnitRole.DEFENDING)
        pass

    def get_assigned_units(self) -> None:
        """Create set of all tags that have been assigned to a role.

        Returns
        -------

        """
        assigned_tags_list: List[int] = []
        for role in self.unit_role_dict:
            assigned_tags_list += self.unit_role_dict[role]
        self.all_assigned_tags = set(assigned_tags_list)

    def catch_unit(self, unit: Unit) -> None:
        """Check if unit is unassigned and give it a role if necessary.

        Parameters
        ----------
        unit :
            Unit that needs a role.

        Returns
        -------

        """
        if unit.type_id in UNIT_TYPES_WITH_NO_ROLE:
            return
        if unit.tag not in self.all_assigned_tags:
            if unit.type_id == self.ai.worker_type:
                self.assign_role(unit.tag, UnitRole.GATHERING)

    def assign_role(
        self, tag: int, role: UnitRole, remove_from_squad: bool = True
    ) -> None:
        """Assign a unit a role.

        Parameters
        ----------
        tag :
            Tag of the unit to be assigned.
        role :
            What role the unit should have.
        remove_from_squad :
            Search for this unit in UnitSquads and remove it.
            Default=True prevents unexpected bugs when using
            UnitSquads

        Returns
        -------

        """
        self.clear_role(tag)
        self.unit_role_dict[role.name].add(tag)
        self.tag_to_role_dict[tag] = role.name
        if remove_from_squad:
            self.manager_mediator.remove_tag_from_squads(tag=tag)

    def batch_assign_role(
        self, tags: Union[List[int], Set[int]], role: UnitRole
    ) -> None:
        """Assign a given role to a List of unit tags.

        Notes
        -----
        Nothing more than a for loop, provided for convenience.

        Parameters
        ----------
        tags :
            Tags of the units to assign to a role.
        role :
            The role the units should be assigned to.

        Returns
        -------

        """
        for tag in tags:
            self.assign_role(tag, role)

    def clear_role(self, tag: int) -> None:
        """Clear a unit's role.

        Parameters
        ----------
        tag :
            Tag of the unit to clear the role of.

        Returns
        -------

        """
        for role in self.unit_role_dict:
            if tag in self.unit_role_dict[role]:
                self.unit_role_dict[role].remove(tag)

    def batch_clear_role(self, tags: Set[int]) -> None:
        """Clear the roles of a given List of unit tags.

        Notes
        -----
        Nothing more than a for loop, provided for convenience.

        Parameters
        ----------
        tags :
            Tags of the units to clear the roles of.

        Returns
        -------

        """
        for tag in tags:
            self.clear_role(tag)

    def get_units_from_role(
        self,
        role: UnitRole,
        unit_type: Optional[Union[UnitID, Set[UnitID]]] = None,
        restrict_to: Optional[Units] = None,
    ) -> Units:
        """Get a Units object containing units with a given role.

        If a UnitID or set of UnitIDs are given, it will only return units of those
        types, otherwise it will return all units with the role. If `restrict_to` is
        specified, it will only retrieve units from that object.


        Parameters
        ----------
        role :
            Role to get units from.
        unit_type :
            Type(s) of units that should be returned. If omitted, all units with the
            role will be returned.
        restrict_to :
            If supplied, only take Units with the given role and type if they also exist
            here.

        Returns
        -------
        Units :
            Units with the given role.

        """
        if unit_type:
            if isinstance(unit_type, UnitID):
                # single unit type, use the single type and role function
                return Units(
                    self.get_single_type_from_single_role(unit_type, role, restrict_to),
                    self.ai,
                )
            else:
                # will crash if not an iterable but we should be careful with typing
                # anyway
                retrieved_units: List[Unit] = []
                for type_id in unit_type:
                    retrieved_units.extend(
                        self.get_single_type_from_single_role(
                            type_id, role, restrict_to
                        )
                    )
                return Units(retrieved_units, self.ai)
        else:
            # get every unit with the role
            if restrict_to:
                tags_to_get: Set[int] = (
                    self.unit_role_dict[role.name] & restrict_to.tags
                )
            else:
                tags_to_get: Set[int] = self.unit_role_dict[role.name]
            # get the List[Unit] from UnitCacheManager and return as Units
            return Units(
                self.manager_mediator.manager_request(
                    ManagerName.UNIT_CACHE_MANAGER,
                    ManagerRequestType.GET_UNITS_FROM_TAGS,
                    tags=tags_to_get,
                ),
                self.ai,
            )

    def get_units_from_roles(
        self,
        roles: Set[UnitRole],
        unit_type: Union[None, UnitID, Set[UnitID]] = None,
    ) -> Units:
        """Get the units matching `unit_type` from the given roles.

        Parameters
        ----------
        roles :
            Roles to get units from.
        unit_type :
            Type(s) of units that should be returned. If omitted, all units with the
            role will be returned.

        Returns
        -------
        Units :
            Units with the given roles.

        """
        retrieved_units = Units([], self.ai)
        for role in roles:
            retrieved_units.extend(self.get_units_from_role(role, unit_type))
        return retrieved_units

    def switch_roles(self, from_role: UnitRole, to_role: UnitRole) -> None:
        """Give all units in a role a different role.

        Parameters
        ----------
        from_role :
            Role the units currently have.
        to_role :
            Role to assign to the units.

        Returns
        -------

        """
        self.batch_assign_role(self.get_units_from_role(from_role).tags, to_role)

    def get_all_from_roles_except(
        self, roles: Set[UnitRole], excluded: Set[UnitID]
    ) -> Units:
        """Get all units from the given roles except for unit types in excluded.

        Parameters
        ----------
        roles :
            Roles to get units from.
        excluded :
            Unit types that should not be included.

        Returns
        -------
        Units :
            Units matching the role that are not of an excluded type.

        """
        role_tags: List[int] = []
        valid_tags: List[int] = []
        # get a list of the tags of the units in the given roles
        for role in roles:
            role_tags.extend(self.unit_role_dict[role.name])
        # convert to a set for faster lookup
        role_set: Set[int] = set(role_tags)
        own_army_dict: Dict = self.manager_mediator.manager_request(
            ManagerName.UNIT_CACHE_MANAGER, ManagerRequestType.GET_CACHED_OWN_ARMY_DICT
        )
        # get the tags of all units that aren't of the excluded types
        for unit_type in own_army_dict:
            if unit_type not in excluded:
                valid_tags.extend(own_army_dict[unit_type].tags)
        shared_tags: List[int] = [tag for tag in valid_tags if tag in role_set]
        return Units(
            self.manager_mediator.manager_request(
                ManagerName.UNIT_CACHE_MANAGER,
                ManagerRequestType.GET_UNITS_FROM_TAGS,
                tags=shared_tags,
            ),
            self.ai,
        )

    def get_single_type_from_single_role(
        self, unit_type: UnitID, role: UnitRole, restrict_to: Optional[Units] = None
    ) -> List[Unit]:
        """Get all units of a given type that have a specified role.

        If restrict_to is Units, this will only get the units of the specified type and
        role that are also in restrict_to.

        Parameters
        ----------
        unit_type :
            Type of unit to retrieve.
        role :
            Role the units should have.
        restrict_to :
            If supplied, only take Units with the given role and type if they also exist
            here.

        Returns
        -------
        List[Unit] :
            Units matching the given type with the given role.

        """
        # get set of tags of units with the role
        unit_with_role_tags: set[int] = self.unit_role_dict[role.name]
        # get the tags of units of the type
        own_cached_army_dict = self.manager_mediator.get_own_army_dict

        units_of_type_tags: set[int] = {u.tag for u in own_cached_army_dict[unit_type]}
        # take the intersection of the sets to get the shared tags
        # this will be the units of the specified type with the specified role
        if not restrict_to:
            shared_tags: set[int] = unit_with_role_tags & units_of_type_tags
        else:
            shared_tags: set[int] = (
                unit_with_role_tags & units_of_type_tags & restrict_to.tags
            )
        # get the List[Unit] from UnitCacheManager
        return self.manager_mediator.manager_request(
            ManagerName.UNIT_CACHE_MANAGER,
            ManagerRequestType.GET_UNITS_FROM_TAGS,
            tags=shared_tags,
        )
