"""Manage general combat tasks.

"""
from typing import Any, Dict, List, Set

from sc2.ids.unit_typeid import UnitTypeId as UnitID
from sc2.position import Point2
from sc2.units import Units

from ..cache import property_cache_once_per_frame
from ..combat.base_unit import BaseUnit
from ..combat.unit_squads import UnitSquads
from ..consts import (
    ATTACK_DISENGAGE_FURTHER_THAN,
    ATTACK_ENGAGE_CLOSER_THAN,
    COMBAT,
    DEBUG,
    MAIN_COMBAT_ROLES,
    EngagementResult,
    ManagerName,
    ManagerRequestType,
    UnitRole,
    UnitTreeQueryType,
)
from ..custom_bot_ai import CustomBotAI
from ..managers.manager import Manager
from ..managers.manager_mediator import IManagerMediator, ManagerMediator


class CombatManager(Manager, IManagerMediator):
    """Control units during combat."""

    ATTACKERS_STEAL_FROM: Set[UnitID] = {}
    EXCLUDED_FROM_A_MOVE: Set[UnitID] = {}

    def __init__(
        self,
        ai: CustomBotAI,
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
        super(CombatManager, self).__init__(ai, config, mediator)

        self.manager_requests_dict = {
            ManagerRequestType.GET_POSITION_OF_MAIN_ATTACKING_SQUAD: lambda kwargs: (
                self.unit_squads.position_of_main_attacking_squad
            ),
            ManagerRequestType.GET_PREDICTED_MAIN_FIGHT_RESULT: lambda kwargs: (
                self.predicted_main_armies_fight_result
            ),
            ManagerRequestType.GET_SQUAD_CLOSE_TO_TARGET: lambda kwargs: (
                self.main_squad_close_to_target
            ),
            ManagerRequestType.REMOVE_TAG_FROM_SQUADS: lambda kwargs: (
                self.unit_squads.remove_tag(kwargs["tag"])
            ),
        }

        self.workers: BaseUnit

        self.EMPTY_UNITS: Units = Units([], self.ai)
        self._init_units()
        self.main_attack_force: Units = self.EMPTY_UNITS
        self.attackers_center_mass: Point2 = self.ai.start_location
        self.blocked_location_to_units_dict: Dict[Point2, Set] = dict()

        self.attack_squad_engages_closer_than: float = self.config[COMBAT][
            ATTACK_ENGAGE_CLOSER_THAN
        ]
        self.attack_squad_disengages_further_than: float = self.config[COMBAT][
            ATTACK_DISENGAGE_FURTHER_THAN
        ]
        self.attack_squad_engage_target: bool = False

        self.unit_controllers: Dict[UnitID, BaseUnit] = {}

        self.unit_squads: UnitSquads = UnitSquads(
            self.ai, self.config, self.manager_mediator, self.unit_controllers
        )

    async def initialise(self) -> None:
        """Set up values that require the bot to be initialised.

        Returns
        -------

        """
        pass

    @property_cache_once_per_frame
    def enemy_main_force_ready(self) -> Units:
        """Enemy units near their center mass.

        Returns
        -------
        Units :
            Enemy units near their center mass.

        """
        enemy_center_mass: Point2 = self.manager_mediator.get_enemy_army_center_mass
        return self.manager_mediator.get_units_in_range(
            positions=[enemy_center_mass],
            distances=14,
            query_tree=UnitTreeQueryType.AllEnemy,
        )[0]

    @property
    def main_squad_close_to_target(self) -> bool:
        """Whether the main squad is close to their target.

        Notes
        -----
        A distance check inside UnitSquad causes hesitation at the distance threshold.
        This keeps track of when a squad is close enough to engage and keeps them
        engaging while inside a leash distance

        Returns
        -------
        bool :
            True if the main squad is within range of their target, False otherwise.

        """
        main_squad_pos: Point2 = self.unit_squads.position_of_main_attacking_squad
        target: Point2 = self.manager_mediator.get_offensive_attack_target
        distance_to_target: float = main_squad_pos.distance_to(target)
        if distance_to_target < self.attack_squad_engages_closer_than:
            self.attack_squad_engage_target = True
        elif distance_to_target > self.attack_squad_disengages_further_than:
            self.attack_squad_engage_target = False

        return self.attack_squad_engage_target

    @property_cache_once_per_frame
    def predicted_main_armies_fight_result(self) -> EngagementResult:
        """Find the main army for each force, and check the combat sim.

        Returns
        -------
        EngagementResult :
            Predicted combat result between friendly and enemy main forces.

        """
        main_own_force: Units = self.manager_mediator.get_units_from_roles(
            roles=MAIN_COMBAT_ROLES
        )

        # try to predict the outcome of the battle
        return self.manager_mediator.can_win_fight(
            own_units=main_own_force, enemy_units=self.enemy_main_force_ready
        )

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

        """
        return self.manager_requests_dict[request](kwargs)

    async def update(self, iteration: int) -> None:
        """Handle combat squads.

        Parameters
        ----------
        iteration :
            The game iteration.

        Returns
        -------

        """
        self._assign_roles()

        self.unit_squads.update(
            self.predicted_main_armies_fight_result,
            self._calculate_role_targets(),
        )

        if self.config[DEBUG]:
            self.ai.draw_text_on_world(
                self.manager_mediator.get_rally_point, "RALLY POINT"
            )

    def handle_dead_units(self, unit_tag: int) -> None:
        """Handle units that have been destroyed.

        Parameters
        ----------
        unit_tag :
            Tag of the unit that was destroyed.

        Returns
        -------

        """
        self.unit_squads.remove_tag(unit_tag)

    def _assign_roles(self) -> None:
        """Provide our main forces roles depending on scenario.

        Returns
        -------

        """
        raise NotImplementedError

    def _calculate_role_targets(self) -> Dict[UnitRole, List[Point2]]:
        """Determine combat targets for each role.

        Returns
        -------
        Dict[UnitRole, List[Point2]] :
            Dictionary of UnitRole to the position that role should target.

        """
        raise NotImplementedError

    def _get_grouping_point(self, our_units: Units) -> Point2:
        """Given our_units, where should they group up?

        Parameters
        ----------
        our_units :
            Friendly units that need to group.

        Returns
        -------
        Point2 :
            Location where the units should group.

        """
        return self.manager_mediator.find_closest_safe_spot(
            from_pos=our_units.center,
            grid=self.manager_mediator.get_ground_grid,
            radius=12,
        )

    def _init_units(self) -> None:
        """Initialize all combat units.

        Returns
        -------

        """
        raise NotImplementedError
