"""Manage strategic decisions.

"""
from collections import defaultdict
from typing import Any, DefaultDict, Dict

from ares.cache import property_cache_once_per_frame
from ares.consts import DEBUG, ManagerName, ManagerRequestType
from ares.custom_bot_ai import CustomBotAI
from ares.managers.manager import Manager
from ares.managers.manager_mediator import IManagerMediator, ManagerMediator
from sc2.ids.unit_typeid import UnitTypeId as UnitID
from sc2.position import Point2
from sc2.units import Units

# from sc2_helper.combat_simulator import CombatSimulator

# add a little health to units in combat sim to avoid division by zero
HEALTH_ADJUSTMENT: float = 0.00000001


class StrategyManager(Manager, IManagerMediator):
    """Anything to do with strategy should go here.

    Examples
    --------
        - army composition
        - should we attack?
        - attack targets

    """

    cached_enemy_army: Units

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
        super().__init__(ai, config, mediator)
        self.manager_requests_dict = {
            # ManagerRequestType.CAN_WIN_FIGHT: lambda kwargs: self.can_win_fight(
            #     **kwargs
            # ),
            ManagerRequestType.GET_ENEMY_AT_HOME: lambda kwargs: self.enemy_at_home,
            ManagerRequestType.GET_OFFENSIVE_ATTACK_TARGET: lambda kwargs: (
                self.offensive_attack_target
            ),
            ManagerRequestType.GET_RALLY_POINT: lambda kwargs: self.rally_point,
            ManagerRequestType.GET_SHOULD_BE_OFFENSIVE: lambda kwargs: (
                self.should_be_offensive
            ),
        }
        self.debug: bool = config[DEBUG]

        self.defensive_attack_target: Point2 = self.ai.start_location
        self.offensive_attack_target: Point2 = self.ai.enemy_start_locations[0]
        # self.combat_sim = CombatSimulator()
        self.cached_enemy_center: Point2 = self.ai.enemy_start_locations[0]
        self.enemy_main_ramp = min(
            (ramp for ramp in self.ai.game_info.map_ramps if len(ramp.upper) in {2, 5}),
            key=lambda r: self.ai.enemy_start_locations[0].distance_to(r.top_center),
        )

        self.own_structures_dict: DefaultDict[UnitID, Units] = defaultdict(Units)

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
        """Update the manager.

        Parameters
        ----------
        iteration :
            The game iteration.

        Returns
        -------

        """
        self.cached_enemy_army = self.manager_mediator.manager_request(
            ManagerName.UNIT_CACHE_MANAGER, ManagerRequestType.GET_CACHED_ENEMY_ARMY
        )
        self.own_structures_dict = self.manager_mediator.get_own_structures_dict

        if iteration % 20 == 0:
            self._update_attack_targets()

        if self.debug:
            self.ai.draw_text_on_world(
                self.offensive_attack_target, "Attack target (o)"
            )

    def _update_attack_targets(self) -> None:
        """Pick what to attack.

        Returns
        -------

        """
        self.offensive_attack_target = self.ai.enemy_start_locations[0]

    @property_cache_once_per_frame
    def enemy_at_home(self) -> bool:
        """Check if the enemy is near their main or natural base.

        Returns
        -------
        bool :
            True if the enemy army center mass is near their main or natural base, False
            otherwise.

        """
        enemy_center_mass: Point2 = self.manager_mediator.get_enemy_army_center_mass
        return (
            self.ai.distance_math_hypot_squared(
                enemy_center_mass, self.ai.enemy_start_locations[0]
            )
            < 625
            or self.ai.distance_math_hypot_squared(
                enemy_center_mass, self.manager_mediator.get_enemy_nat
            )
            < 400
        )

    @property_cache_once_per_frame
    def rally_point(self) -> Point2:
        """Identify a rally point for units.

        Returns
        -------
        Point2 :
            Position to use as a rally point.

        """
        return self.ai.main_base_ramp.top_center

    @property_cache_once_per_frame
    def should_be_offensive(self) -> bool:
        """Under what conditions should we launch an offensive attack on the enemy.

        Returns
        -------
        bool :
            True if we should launch an attack, False otherwise.

        """
        return self.ai.supply_used == 200
