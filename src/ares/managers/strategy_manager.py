"""Manage strategic decisions.

"""
from collections import defaultdict
from typing import Any, DefaultDict, Dict, Tuple

from consts import DEBUG, BotMode, EngagementResult, ManagerName, ManagerRequestType
from custom_bot_ai import CustomBotAI
from managers.manager import Manager
from managers.manager_mediator import IManagerMediator, ManagerMediator
from sc2.ids.unit_typeid import UnitTypeId as UnitID
from sc2.position import Point2
from sc2.units import Units

from cache import property_cache_once_per_frame
from sc2_helper.combat_simulator import CombatSimulator

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

    bot_mode: BotMode
    cached_enemy_army: Units
    starting_bot_mode: BotMode

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
            ManagerRequestType.CAN_WIN_FIGHT: lambda kwargs: self.can_win_fight(
                **kwargs
            ),
            ManagerRequestType.GET_BOT_MODE: lambda kwargs: self.bot_mode,
            ManagerRequestType.GET_ENEMY_AT_HOME: lambda kwargs: self.enemy_at_home,
            ManagerRequestType.GET_OFFENSIVE_ATTACK_TARGET: lambda kwargs: (
                self.offensive_attack_target
            ),
            ManagerRequestType.GET_RALLY_POINT: lambda kwargs: self.rally_point,
            ManagerRequestType.GET_SHOULD_BE_OFFENSIVE: lambda kwargs: (
                self.should_be_offensive
            ),
            ManagerRequestType.GET_STARTING_BOT_MODE: lambda kwargs: (
                self.starting_bot_mode
            ),
        }
        self.debug: bool = config[DEBUG]

        self.defensive_attack_target: Point2 = self.ai.start_location
        self.offensive_attack_target: Point2 = self.ai.enemy_start_locations[0]
        self.combat_sim = CombatSimulator()
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

    async def initialise(self) -> None:
        """Set up values that require the bot to be initialised.

        Returns
        -------

        """
        self.bot_mode = self.starting_bot_mode = self.manager_mediator.manager_request(
            ManagerName.DATA_MANAGER, ManagerRequestType.GET_INITIAL_BOT_MODE
        )

    def _update_attack_targets(self) -> None:
        """Pick what to attack.

        Returns
        -------

        """
        self.offensive_attack_target = self.ai.enemy_start_locations[0]

    def can_win_fight(
        self,
        own_units: Units,
        enemy_units: Units,
        timing_adjust: bool = True,
        good_positioning: bool = False,
    ) -> EngagementResult:
        """Use the combat simulator to predict if our units can beat the enemy units.

        Returns an Enum so that thresholds can be easily adjusted and it may be easier
        to read the results in other code.

        Warnings
        --------
        The combat simulator has some bugs in it that I'm not able to fix since they're
        in the Rust code. Notable bugs include Missile Turrets shooting Hydralisks and
        45 SCVs killing a Mutalisk. To get around this, you can filter out units that
        shouldn't be included, such as not including SCVs when seeing if the Mutalisks
        can win a fight (this creates its own problems due to the bounce, but I don't
        believe the bounce is included in the simulation). The simulator isn't perfect,
        but I think it's still usable. My recommendation is to use it cautiously and
        only when all units involved can attack each other. It definitely doesn't factor
        good micro in, so anything involving spell casters is probably a bad idea.

        Parameters
        ----------
        own_units :
            Friendly units to us in the simulation.
        enemy_units :
            Enemy units to us in the simulation.
        timing_adjust :
            Take distance between units into account.
        good_positioning :
            Assume units are positioned reasonably.

        Returns
        -------
        EngagementResult :
            Predicted result of the engagement.

        """
        self.combat_sim.enable_timing_adjustment(timing_adjust)
        self.combat_sim.assume_reasonable_positioning(good_positioning)
        result: Tuple[bool, float] = self.combat_sim.predict_engage(
            own_units, enemy_units
        )

        own_health: float
        enemy_health: float
        own_health, enemy_health = (
            sum([u.health for u in own_units]) + HEALTH_ADJUSTMENT,
            sum([u.health + u.shield for u in enemy_units]) + HEALTH_ADJUSTMENT,
        )
        # if the winning units are at 10% health after the fight, the actual engagement
        # will be determined by micro
        if result[0]:
            health_percentage = result[1] / own_health
            if health_percentage >= 0.9:
                return EngagementResult.VICTORY_EMPHATIC
            elif health_percentage >= 0.75:
                return EngagementResult.VICTORY_OVERWHELMING
            elif health_percentage >= 0.6:
                return EngagementResult.VICTORY_DECISIVE
            elif health_percentage > 0.4:
                return EngagementResult.VICTORY_CLOSE
            elif health_percentage > 0.2:
                return EngagementResult.VICTORY_MARGINAL
        else:
            health_percentage = result[1] / enemy_health
            if health_percentage >= 0.9:
                return EngagementResult.LOSS_EMPHATIC
            elif health_percentage >= 0.75:
                return EngagementResult.LOSS_OVERWHELMING
            elif health_percentage > 0.6:
                return EngagementResult.LOSS_DECISIVE
            elif health_percentage > 0.4:
                return EngagementResult.LOSS_CLOSE
            elif health_percentage > 0.2:
                return EngagementResult.LOSS_MARGINAL
        # no previous condition was met
        return EngagementResult.TIE

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
