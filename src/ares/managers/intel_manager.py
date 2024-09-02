from typing import TYPE_CHECKING, Any

from cython_extensions import cy_distance_to_squared
from loguru import logger
from sc2.data import Race
from sc2.ids.unit_typeid import UnitTypeId as UnitID
from sc2.unit import Unit
from sc2.units import Units

from ares.cache import property_cache_once_per_frame
from ares.consts import (
    TOWNHALL_TYPES,
    WORKER_TYPES,
    ManagerRequestType,
    UnitTreeQueryType,
)
from ares.managers.manager import Manager
from ares.managers.manager_mediator import IManagerMediator, ManagerMediator

if TYPE_CHECKING:
    from ares import AresBot


class IntelManager(Manager, IManagerMediator):
    def __init__(
        self,
        ai: "AresBot",
        config: dict,
        mediator: ManagerMediator,
    ) -> None:
        """Gather intelligence on the enemy.

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
            ManagerRequestType.GET_ENEMY_EXPANDED: lambda kwargs: (
                self.get_enemy_expanded
            ),
            ManagerRequestType.GET_ENEMY_HAS_BASE_OUTSIDE_NATURAL: lambda kwargs: (
                self.get_enemy_has_base_outside_natural
            ),
            ManagerRequestType.GET_ENEMY_FOUR_GATE: lambda kwargs: (
                self.get_enemy_four_gate
            ),
            ManagerRequestType.GET_ENEMY_LING_RUSHED: lambda kwargs: (
                self.enemy_ling_rushed
            ),
            ManagerRequestType.GET_ENEMY_MARAUDER_RUSH: lambda kwargs: (
                self.get_enemy_marauder_rush
            ),
            ManagerRequestType.GET_ENEMY_MARINE_RUSH: lambda kwargs: (
                self.get_enemy_marine_rush
            ),
            ManagerRequestType.GET_ENEMY_RAVAGER_RUSH: lambda kwargs: (
                self.get_enemy_ravager_rush
            ),
            ManagerRequestType.GET_ENEMY_ROACH_RUSHED: lambda kwargs: (
                self.enemy_roach_rushed
            ),
            ManagerRequestType.GET_ENEMY_WAS_GREEDY: lambda kwargs: (
                self.get_enemy_was_greedy
            ),
            ManagerRequestType.GET_ENEMY_WENT_FOUR_GATE: lambda kwargs: (
                self.get_enemy_went_four_gate
            ),
            ManagerRequestType.GET_ENEMY_WENT_MARINE_RUSH: lambda kwargs: (
                self.get_enemy_went_marine_rush
            ),
            ManagerRequestType.GET_ENEMY_WENT_MARAUDER_RUSH: lambda kwargs: (
                self.get_enemy_went_marauder_rush
            ),
            ManagerRequestType.GET_ENEMY_WENT_REAPER: lambda kwargs: (
                self.enemy_went_reaper
            ),
            ManagerRequestType.GET_ENEMY_WORKER_RUSHED: lambda kwargs: (
                self.enemy_worker_rushed
            ),
            ManagerRequestType.GET_IS_PROXY_ZEALOT: lambda kwargs: self.is_proxy_zealot,
        }

        self.enemy_ling_rushed: bool = False
        self.enemy_roach_rushed: bool = False
        self.get_enemy_was_greedy: bool = False
        self.get_enemy_went_four_gate: bool = False
        self.get_enemy_went_marauder_rush: bool = False
        self.get_enemy_went_marine_rush: bool = False
        self.enemy_went_reaper: bool = False
        self.enemy_worker_rushed: bool = False

    def manager_request(
        self,
        receiver: str,
        request: ManagerRequestType,
        reason: str = None,
        **kwargs,
    ) -> Any:
        """Fetch information from this Manager.

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
        Optional[Union[Dict, DefaultDict, Coroutine[Any, Any, bool]]] :
            Everything that could possibly be returned from the Manager fits in there

        """
        if self.ai.arcade_mode:
            logger.warning(
                f"Mediator requests to intel manager doesn't work on arcade mode."
                f"The following request will return None: {request}"
            )
            return
        return self.manager_requests_dict[request](kwargs)

    @property_cache_once_per_frame
    def get_enemy_expanded(self) -> bool:
        """Has the enemy expanded?

        Returns
        -------
        bool
        """
        return (
            len(
                [
                    s
                    for s in self.ai.enemy_structures
                    if s.type_id in TOWNHALL_TYPES
                    and cy_distance_to_squared(
                        s.position, self.ai.enemy_start_locations[0]
                    )
                    > 36.0
                ]
            )
            > 0
        )

    @property_cache_once_per_frame
    def get_enemy_has_base_outside_natural(self) -> bool:
        """Check for enemy expansions outside enemy natural.

        Returns
        -------
        bool
        """
        return (
            len(
                [
                    s
                    for s in self.ai.enemy_structures
                    if s.type_id in TOWNHALL_TYPES
                    and cy_distance_to_squared(
                        s.position, self.ai.enemy_start_locations[0]
                    )
                    > 36.0
                    and cy_distance_to_squared(
                        s.position, self.manager_mediator.get_enemy_nat
                    )
                    > 36.0
                ]
            )
            > 0
        )

    @property_cache_once_per_frame
    def get_enemy_marauder_rush(self) -> bool:
        """marauder rush?

        Returns
        -------
        bool
        """
        if self.ai.enemy_race != Race.Terran or self.ai.time > 240.0:
            return False

        num_marauders: int = len(
            self.manager_mediator.get_enemy_army_dict[UnitID.MARAUDER]
        )
        proxies: list[Unit] = [
            p
            for p in self.ai.get_enemy_proxies(55.0, self.manager_mediator.get_own_nat)
            if p.type_id == UnitID.BARRACKSTECHLAB
        ]
        if (
            len(proxies) > 0
            or (self.ai.time < 210.0 and num_marauders >= 2)
            or (self.ai.time < 160.0 and num_marauders >= 1)
        ):
            if not self.get_enemy_went_marauder_rush:
                logger.info(f"{self.ai.time_formatted}: marauder rush detected")
            self.get_enemy_went_marauder_rush = True
            return True

    @property_cache_once_per_frame
    def get_enemy_four_gate(self) -> bool:
        """four gate?

        Returns
        -------
        bool
        """
        if (
            self.ai.enemy_race != Race.Protoss
            or self.ai.time > 210.0
            or len(self.ai.enemy_structures(TOWNHALL_TYPES)) >= 2
        ):
            return False

        four_gate: bool = (
            self.ai.time < 200.0
            and len(
                [s for s in self.ai.enemy_structures if s.type_id == UnitID.GATEWAY]
            )
            >= 3
        )
        if four_gate:
            if not self.get_enemy_went_four_gate:
                logger.info(f"{self.ai.time_formatted}: Four gate detected")
            self.get_enemy_went_four_gate = True
        return four_gate

    @property_cache_once_per_frame
    def get_enemy_marine_rush(self) -> bool:
        """marine rush?

        Returns
        -------
        bool
        """
        if (
            self.ai.enemy_race != Race.Terran
            or len(self.ai.enemy_structures(TOWNHALL_TYPES)) >= 2
            or self.ai.time > 210.0
        ):
            return False

        if self.ai.enemy_structures(UnitID.FACTORY):
            return False
        num_marines: int = len(
            [
                m
                for m in self.manager_mediator.get_enemy_army_dict[UnitID.MARINE]
                if cy_distance_to_squared(m.position, self.ai.enemy_start_locations[0])
                > 3600.0
            ]
        )
        marine_threshold: int = int(int(self.ai.time) / 45)
        marine_rush: bool = (
            self.ai.time < 180.0
            and len(
                [s for s in self.ai.enemy_structures if s.type_id == UnitID.BARRACKS]
            )
            >= 3
        ) or (
            self.ai.time < 300.0
            and num_marines >= marine_threshold
            and num_marines >= 3
        )
        if marine_rush:
            if not self.get_enemy_went_marine_rush:
                logger.info(f"{self.ai.time_formatted}: Marine rush detected")
            self.get_enemy_went_marine_rush = True
        return marine_rush

    @property_cache_once_per_frame
    def get_enemy_ravager_rush(self) -> bool:
        """ravager rush?

        Returns
        -------
        bool
        """
        if self.ai.enemy_race == Race.Zerg:
            num_ravagers: int = len(
                self.manager_mediator.get_enemy_army_dict[UnitID.RAVAGER]
            )
            if self.ai.time < 240.0 and num_ravagers > 0:
                return True
        return False

    @property
    def is_proxy_zealot(self) -> bool:
        """Is proxy gateways?

        Returns
        -------
        bool
        """
        if self.ai.enemy_race != Race.Protoss or self.ai.time > 240:
            return False

        num_proxy_gateways: int = self.ai.enemy_structures.filter(
            lambda s: s.type_id == UnitID.GATEWAY
            and cy_distance_to_squared(self.ai.start_location, s.position) < 10000.0
            and cy_distance_to_squared(self.ai.enemy_start_locations[0], s.position)
            > 3600.0
        ).amount
        proxy_zealots: list[Unit] = [
            z
            for z in self.ai.enemy_units
            if z.type_id == UnitID.ZEALOT
            and cy_distance_to_squared(z.position, self.ai.start_location) < 4225
        ]
        if num_proxy_gateways >= 2 or (
            self.ai.time < 150.0 and len(proxy_zealots) >= 1
        ):
            return True
        return False

    async def update(self, iteration: int) -> None:
        if self.ai.arcade_mode:
            return

        self._check_for_enemy_rush()

        if (
            self.ai.enemy_race == Race.Terran
            and not self.enemy_went_reaper
            and len(self.manager_mediator.get_enemy_army_dict[UnitID.REAPER]) > 0
        ):
            self.enemy_went_reaper = True

    def _check_for_enemy_rush(self):
        if self.ai.enemy_race == Race.Zerg and not self.enemy_ling_rushed:
            enemy_lings: list[Unit] = self.manager_mediator.get_enemy_army_dict[
                UnitID.ZERGLING
            ]
            if (
                self.ai.time < 150.0
                and len(
                    [
                        ling
                        for ling in enemy_lings
                        if cy_distance_to_squared(ling.position, self.ai.start_location)
                        < 2500.0
                    ]
                )
                > 2
            ):
                logger.info(f"{self.ai.time}: enemy ling rush detected")
                self.enemy_ling_rushed = True

            if self.ai.time < 180.0 and len(enemy_lings) > 7:
                logger.info(f"{self.ai.time}: enemy ling rush detected")
                self.enemy_ling_rushed = True

            if self.ai.time < 90.0 and len(enemy_lings) > 4:
                logger.info(f"{self.ai.time}: enemy ling rush detected")
                self.enemy_ling_rushed = True

        if self.ai.enemy_race == Race.Zerg and not self.enemy_roach_rushed:
            if (
                self.ai.time < 240.0
                and len(
                    [
                        ling
                        for ling in self.manager_mediator.get_enemy_army_dict[
                            UnitID.ROACH
                        ]
                        if cy_distance_to_squared(ling.position, self.ai.start_location)
                        < 2500.0
                    ]
                )
                >= 6
            ):
                logger.info(f"{self.ai.time}: enemy roach rush detected")
                self.enemy_roach_rushed = True

            if (
                self.ai.time < 180.0
                and len(self.manager_mediator.get_enemy_army_dict[UnitID.ROACH]) >= 3
            ):
                logger.info(f"{self.ai.time}: enemy roach rush detected")
                self.enemy_roach_rushed = True

        if not self.enemy_worker_rushed and self.ai.time < 180.0:
            near_enemy_workers: Units = self.manager_mediator.get_units_in_range(
                start_points=[self.ai.start_location],
                distances=[15],
                query_tree=UnitTreeQueryType.EnemyGround,
            )[0].filter(lambda u: u.type_id in WORKER_TYPES)
            if len(near_enemy_workers) >= 6:
                logger.info(f"{self.ai.time}: worker rush detected")
                self.enemy_worker_rushed = True
