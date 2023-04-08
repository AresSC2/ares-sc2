"""The core of the bot.

"""

from typing import TYPE_CHECKING, Dict, List, Union

from consts import DEBUG, UnitRole
from custom_bot_ai import CustomBotAI
from managers.ability_tracker_manager import AbilityTrackerManager
from managers.building_manager import BuildingManager
from managers.data_manager import DataManager
from managers.manager_mediator import ManagerMediator
from managers.path_manager import PathManager
from managers.production_manager import ProductionManager
from managers.resource_manager import ResourceManager
from managers.strategy_manager import StrategyManager
from managers.terrain_manager import TerrainManager
from managers.unit_cache_manager import UnitCacheManager
from managers.unit_memory_manager import UnitMemoryManager
from managers.unit_role_manager import UnitRoleManager
from sc2.data import Result
from sc2.unit import Unit

if TYPE_CHECKING:
    from ..managers.manager import Manager


class Hub:
    """The main manager "hub", where all the managers come together.

    In this file an instance of each manager is created.
    On each step / frame, the managers `update` method is called
    """

    def __init__(self, ai: CustomBotAI, config: Dict) -> None:
        """Initialise Manager objects and set update priority.

        Parameters
        ----------
        ai :
            Bot object that will be running the game
        config :
            Dictionary with the data from the configuration file

        """
        self.ai: CustomBotAI = ai
        self.debug: bool = config[DEBUG]
        self.config: Dict = config
        self.manager_mediator: ManagerMediator = ManagerMediator()

        self.data_manager: DataManager = DataManager(ai, config, self.manager_mediator)
        self.unit_cache_manager: UnitCacheManager = UnitCacheManager(
            ai, config, self.manager_mediator
        )
        self.ability_tracker_manager = AbilityTrackerManager(
            ai, config, self.manager_mediator
        )
        self.unit_role_manager: UnitRoleManager = UnitRoleManager(
            ai, config, self.manager_mediator
        )
        self.unit_memory_manager: UnitMemoryManager = UnitMemoryManager(
            ai, config, self.manager_mediator
        )
        self.path_manager: PathManager = PathManager(ai, config, self.manager_mediator)
        self.terrain_manager: TerrainManager = TerrainManager(
            ai, config, self.manager_mediator
        )
        self.strategy_manager: StrategyManager = StrategyManager(
            ai, config, self.manager_mediator
        )
        self.resource_manager: ResourceManager = ResourceManager(
            ai, config, self.manager_mediator
        )
        self.building_manager: BuildingManager = BuildingManager(
            ai, config, self.manager_mediator
        )
        self.production_manager: ProductionManager = ProductionManager(
            ai, config, self.manager_mediator
        )
        # in order of priority
        self.managers: List["Manager"] = [
            self.data_manager,
            self.unit_role_manager,
            self.unit_cache_manager,
            self.unit_memory_manager,
            self.path_manager,
            self.strategy_manager,
            self.terrain_manager,
            self.resource_manager,
            self.building_manager,  # must be updated before production manager
            self.production_manager,
            self.ability_tracker_manager,
        ]

        # manager mediator needs a reference to all the managers
        self.manager_mediator.add_managers(self.managers)

    async def init_managers(self) -> None:
        """Intialise manager data that requires the game to have started.

        Some Managers require information, such as enemy base locations, that isn't
        available until the game has launched. This is allows that information to be
        collected before any game actions are taken.

        Returns
        -------

        """
        for manager in self.managers:
            await manager.initialise()

    async def on_unit_destroyed(self, unit_tag: int) -> None:
        """Call the manager functions to handle destroyed units.

        Parameters
        ----------
        unit_tag :
            The tag of the unit that was destroyed.

        Returns
        -------

        """
        self.unit_cache_manager.remove_unit(unit_tag)
        self.unit_memory_manager.remove_unit(unit_tag)
        self.unit_role_manager.clear_role(unit_tag)
        # remove dead townhalls and workers
        self.resource_manager.on_unit_destroyed(unit_tag)

        if unit_tag in self.building_manager.building_tracker:
            self.building_manager.remove_unit(unit_tag)

    def on_game_end(self, result: Union[Result, str]) -> None:
        """Store data from the completed game.

        Parameters
        ----------
        result :
            The game result.

        Returns
        -------

        """
        self.data_manager.store_opponent_data(result)

    async def on_structure_complete(self, unit: Unit) -> None:
        """On structure completion event (own units)

        Parameters
        ----------
        unit :
            The Unit that just finished building

        Returns
        -------

        """
        pass

    async def on_unit_created(self, unit: Unit) -> None:
        """On unit created event (own units)

        Parameters
        ----------
        unit :
            The Unit that was just created

        Returns
        -------

        """
        pass

    async def on_unit_took_damage(self, unit: Unit) -> None:
        """On unit or structure taking damage

        Parameters
        ----------
        unit :
            The Unit that took damage

        Returns
        -------

        """
        pass

    async def update_managers(self, iteration: int) -> None:
        """Update managers, reset grids, and draw any debugs.

        Parameters
        ----------
        iteration :
            The game iteration.

        Returns
        -------

        """
        for manager in self.managers:
            await manager.update(iteration)

        # we have finished with the grids, reset them before the next step
        self.path_manager.reset_grids(iteration)

        if self.debug:
            self._debug_draw()

    def _debug_draw(self) -> None:
        """Draw debug information to the screen.

        Returns
        -------

        """
        # left hand side
        self.ai.client.debug_text_screen(
            f"Workers per gas: \
            {str(self.resource_manager.workers_per_gas)}",
            pos=(0.05, 0.14),
            size=13,
            color=(0, 255, 255),
        )

        self.ai.client.debug_text_screen(
            "UNIT ROLE TAGS",
            pos=(0.05, 0.28),
            size=13,
            color=(0, 255, 255),
        )
        self.ai.client.debug_text_screen(
            f"Base Defenders: \
            {str(self.unit_role_manager.unit_role_dict[UnitRole.BASE_DEFENDER])}",
            pos=(0.05, 0.30),
            size=13,
            color=(0, 255, 255),
        )

        # right hand side
        self.ai.client.debug_text_screen(
            f"Enemy Army Value: {self.unit_cache_manager.enemy_army_value}",
            pos=(0.85, 0.1),
            size=13,
            color=(0, 255, 255),
        )
        self.ai.client.debug_text_screen(
            f"Ready Army Value: {self.unit_cache_manager.ready_army_value}",
            pos=(0.85, 0.11),
            size=13,
            color=(0, 255, 255),
        )
        self.ai.client.debug_text_screen(
            f"Total Army Value: {self.unit_cache_manager.own_army_value}",
            pos=(0.85, 0.12),
            size=13,
            color=(0, 255, 255),
        )

        self.ai.client.debug_text_screen(
            f"Mineral collection rate: {self.ai.state.score.collection_rate_minerals}",
            pos=(0.85, 0.17),
            size=13,
            color=(0, 255, 255),
        )

        self.ai.client.debug_text_screen(
            f"Vespene collection rate: {self.ai.state.score.collection_rate_vespene}",
            pos=(0.85, 0.18),
            size=13,
            color=(0, 255, 255),
        )

        self.ai.client.debug_text_screen(
            f"Workers per gas: {self.resource_manager.workers_per_gas}",
            pos=(0.85, 0.2),
            size=13,
            color=(0, 255, 255),
        )
