"""
WARNING:
    The combat simulator has some bugs in it that I'm not able to fix
    since they're in the Rust code. Notable bugs include Missile Turrets
    shooting Hydralisks and 45 SCVs killing a Mutalisk. To get around
    this, you can filter out units that shouldn't be included, such as not
    including SCVs when seeing if the Mutalisks can win a fight (this
    creates its own problems due to the bounce, but I don't believe the bounce
    is included in the simulation). The simulator isn't perfect, but I
    think it's still usable. My recommendation is to use it cautiously and
    only when all units involved can attack each other. It definitely doesn't
    factor good micro in, so anything involving spell casters is probably a bad idea.
    - IDPTG/Paul
"""

from typing import TYPE_CHECKING, Any

from sc2.units import Units

from ares.consts import EngagementResult, ManagerName, ManagerRequestType
from ares.managers.manager import Manager
from ares.managers.manager_mediator import IManagerMediator, ManagerMediator
from sc2_helper.combat_simulator import CombatSimulator

if TYPE_CHECKING:
    from ares import AresBot


class CombatSimManager(Manager, IManagerMediator):
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
        """
        super(CombatSimManager, self).__init__(ai, config, mediator)

        self.combat_sim: CombatSimulator = CombatSimulator()

        self.manager_requests_dict = {
            ManagerRequestType.CAN_WIN_FIGHT: lambda kwargs: self.can_win_fight(
                **kwargs
            )
        }

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
        """
        Parameters
        ----------
        iteration :
            The game iteration.

        Returns
        -------

        """
        pass

    def can_win_fight(
        self,
        own_units: Units,
        enemy_units: Units,
        timing_adjust: bool = True,
        good_positioning: bool = False,
        workers_do_no_damage: bool = False,
    ) -> EngagementResult:
        """
        Use the combat simulator to predict if our units can beat the enemy units.

        Returns an Enum so that thresholds can be easily adjusted
        and it may be easier to read the results in other code.

        Parameters
        ----------
        own_units :
            Our units involved in the battle.
        enemy_units
            The enemy units.
        timing_adjust :
            Take distance between units into account.
        good_positioning :
            Assume units are decently split.
        workers_do_no_damage :
            Don't take workers into account.

        Returns
        -------
        EngagementResult :
            Enum with human-readable engagement result

        """
        self.combat_sim.enable_timing_adjustment(timing_adjust)
        self.combat_sim.assume_reasonable_positioning(good_positioning)
        self.combat_sim.workers_do_no_damage(workers_do_no_damage)
        result: tuple[bool, float] = self.combat_sim.predict_engage(
            own_units, enemy_units
        )

        own_health: float
        enemy_health: float
        own_health, enemy_health = (
            sum([u.health for u in own_units]) + 1e-16,
            sum([u.health + u.shield for u in enemy_units]) + 1e-16,
        )
        # if the winning units are at 10% health after the fight,
        # the actual engagement will be determined by micro
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
