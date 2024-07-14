"""The core of the bot.

"""

from typing import TYPE_CHECKING, Dict, List, Optional, Union

from sc2.data import Result
from sc2.unit import Unit

from ares.consts import DEBUG
from ares.managers.ability_tracker_manager import AbilityTrackerManager
from ares.managers.building_manager import BuildingManager
from ares.managers.combat_sim_manager import CombatSimManager
from ares.managers.data_manager import DataManager
from ares.managers.enemy_to_base_manager import EnemyToBaseManager
from ares.managers.flying_structure_manager import FlyingStructureManager
from ares.managers.intel_manager import IntelManager
from ares.managers.manager_mediator import ManagerMediator
from ares.managers.path_manager import PathManager
from ares.managers.placement_manager import PlacementManager
from ares.managers.resource_manager import ResourceManager
from ares.managers.squad_manager import SquadManager
from ares.managers.terrain_manager import TerrainManager
from ares.managers.unit_cache_manager import UnitCacheManager
from ares.managers.unit_memory_manager import UnitMemoryManager
from ares.managers.unit_role_manager import UnitRoleManager

if TYPE_CHECKING:
    from ares import AresBot
    from ares.managers.manager import Manager


class Hub:
    """The main manager "hub", where all the managers come together.

    In this file an instance of each manager is created.
    On each step / frame, the managers `update` method is called
    """

    def __init__(
        self,
        ai: "AresBot",
        config: Dict,
        manager_mediator: ManagerMediator,
        data_manager: DataManager = None,
        enemy_to_base_manager: EnemyToBaseManager = None,
        unit_cache_manager: UnitCacheManager = None,
        ability_tracker_manager: AbilityTrackerManager = None,
        intel_manager: IntelManager = None,
        unit_role_manager: UnitRoleManager = None,
        unit_memory_manager: UnitMemoryManager = None,
        placement_manager: PlacementManager = None,
        path_manager: PathManager = None,
        terrain_manager: TerrainManager = None,
        resource_manager: ResourceManager = None,
        building_manager: BuildingManager = None,
        additional_managers: Optional[List["Manager"]] = None,
    ) -> None:
        """Initialise Manager objects and set update priority.

        Parameters
        ----------
        ai :
            Bot object that will be running the game
        config :
            Dictionary with the data from the configuration file
        manager_mediator :
            ManagerMediator class for inter-Manager communication
        data_manager :
            Optional DataManager override
        enemy_to_base_manager :
            Optional EnemyToBaseManager override
        unit_cache_manager :
            Optional UnitCacheManager override
        ability_tracker_manager :
            Optional AbilityTrackerManager override
        unit_role_manager :
            Optional UnitRoleManager override
        unit_memory_manager :
            Optional UnitMemoryManager override
        placement_manager :
            Optional PlacementManager override
        path_manager :
            Optional PathManager override
        terrain_manager :
            Optional TerrainManager override
        resource_manager :
            Optional ResourceManager override
        building_manager :
            Optional BuildingManager override
        additional_managers :
            Additional custom managers

        """
        self.ai: "AresBot" = ai
        self.debug: bool = config[DEBUG]
        self.config: Dict = config
        self.manager_mediator: ManagerMediator = manager_mediator

        self.data_manager: DataManager = (
            DataManager(ai, config, self.manager_mediator)
            if not data_manager
            else data_manager
        )
        self.unit_cache_manager: UnitCacheManager = (
            UnitCacheManager(ai, config, self.manager_mediator)
            if not unit_cache_manager
            else unit_cache_manager
        )
        self.ability_tracker_manager: AbilityTrackerManager = (
            AbilityTrackerManager(ai, config, self.manager_mediator)
            if not ability_tracker_manager
            else ability_tracker_manager
        )
        self.intel_manager: IntelManager = (
            IntelManager(ai, config, self.manager_mediator)
            if not intel_manager
            else intel_manager
        )
        self.unit_role_manager: UnitRoleManager = (
            UnitRoleManager(ai, config, self.manager_mediator)
            if not unit_role_manager
            else unit_role_manager
        )
        self.unit_memory_manager: UnitMemoryManager = (
            UnitMemoryManager(ai, config, self.manager_mediator)
            if not unit_memory_manager
            else unit_memory_manager
        )
        self.placement_manager: PlacementManager = (
            PlacementManager(ai, config, self.manager_mediator)
            if not placement_manager
            else placement_manager
        )
        self.path_manager: PathManager = (
            PathManager(ai, config, self.manager_mediator)
            if not path_manager
            else path_manager
        )
        self.terrain_manager: TerrainManager = (
            TerrainManager(ai, config, self.manager_mediator)
            if not terrain_manager
            else terrain_manager
        )
        self.resource_manager: ResourceManager = (
            ResourceManager(ai, config, self.manager_mediator)
            if not resource_manager
            else resource_manager
        )
        self.building_manager: BuildingManager = (
            BuildingManager(ai, config, self.manager_mediator)
            if not building_manager
            else building_manager
        )
        self.enemy_to_base_manager: EnemyToBaseManager = (
            EnemyToBaseManager(ai, config, self.manager_mediator)
            if not enemy_to_base_manager
            else enemy_to_base_manager
        )
        self.combat_sim_manager: CombatSimManager = CombatSimManager(
            ai, config, self.manager_mediator
        )
        self.flying_structures_manager: FlyingStructureManager = FlyingStructureManager(
            ai, config, self.manager_mediator
        )
        self.squad_manager: SquadManager = SquadManager(
            ai, config, self.manager_mediator
        )

        # in order of priority
        self.managers: list["Manager"] = [
            self.data_manager,
            self.unit_role_manager,
            self.unit_cache_manager,
            self.unit_memory_manager,
            self.path_manager,
            self.terrain_manager,
            self.resource_manager,
            self.building_manager,
            self.ability_tracker_manager,
            self.placement_manager,
            self.enemy_to_base_manager,
            self.intel_manager,
            self.combat_sim_manager,
            self.flying_structures_manager,
            self.squad_manager,
        ]

        if additional_managers:
            for manager in additional_managers:
                self.managers.append(manager)

        # manager mediator needs a reference to all the managers
        self.manager_mediator.add_managers(self.managers)

    def init_managers(self) -> None:
        """Intialise manager data that requires the game to have started.

        Some Managers require information, such as enemy base locations, that isn't
        available until the game has launched. This is allows that information to be
        collected before any game actions are taken.

        Returns
        -------

        """
        for manager in self.managers:
            manager.initialise()

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
        self.placement_manager.on_building_destroyed(unit_tag)
        # self.building_manager.remove_unit(unit_tag)

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
        """
        pass

    def on_building_started(self, unit: Unit) -> None:
        """On structure starting

        Parameters
        ----------
        unit :
        """
        self.placement_manager.on_building_started(unit)

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
