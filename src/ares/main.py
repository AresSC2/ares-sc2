from collections import defaultdict
from os import getcwd, path
from typing import DefaultDict, Dict, List, Optional, Set, Tuple, Union

import yaml
from cython_extensions import cy_unit_pending
from loguru import logger
from s2clientprotocol.raw_pb2 import Unit as RawUnit
from sc2.constants import ALL_GAS, IS_PLACEHOLDER, FakeEffectID, geyser_ids, mineral_ids
from sc2.data import Race, Result, race_gas, race_townhalls, race_worker
from sc2.dicts.unit_train_build_abilities import TRAIN_INFO
from sc2.game_data import Cost
from sc2.game_state import EffectData
from sc2.ids.ability_id import AbilityId
from sc2.ids.buff_id import BuffId
from sc2.ids.unit_typeid import UnitTypeId as UnitID
from sc2.ids.upgrade_id import UpgradeId
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units

from ares.behavior_exectioner import BehaviorExecutioner
from ares.behaviors.behavior import Behavior
from ares.build_runner.build_order_runner import BuildOrderRunner
from ares.config_parser import ConfigParser
from ares.consts import (
    ADD_ONS,
    ADD_SHADES_ON_FRAME,
    ALL_STRUCTURES,
    CHAT_DEBUG,
    DEBUG,
    DEBUG_GAME_STEP,
    DEBUG_OPTIONS,
    GAME_STEP,
    GATEWAY_UNITS,
    ID,
    IGNORE_DESTRUCTABLES,
    RACE_SUPPLY,
    SHADE_COMMENCED,
    SHADE_DURATION,
    SHADE_OWNER,
    TECHLAB_TYPES,
    UNITS_TO_AVOID_TYPES,
    USE_DATA,
    WORKER_TYPES,
    UnitRole,
    UnitTreeQueryType,
)
from ares.custom_bot_ai import CustomBotAI
from ares.dicts.cost_dict import COST_DICT
from ares.dicts.enemy_detector_ranges import DETECTOR_RANGES
from ares.dicts.enemy_vs_ground_static_defense_ranges import (
    ENEMY_VS_GROUND_STATIC_DEFENSE_TYPES,
)
from ares.managers.hub import Hub
from ares.managers.manager_mediator import ManagerMediator


class AresBot(CustomBotAI):
    """Final setup of CustomBotAI for usage.

    Most bot logic should go in Hub.
    """

    behavior_executioner: BehaviorExecutioner  # executes behaviors on each step
    build_order_runner: BuildOrderRunner  # execute exact build order from config
    cost_dict: Dict[UnitID, Cost]  #: UnitTypeId to cost for faster lookup later
    manager_hub: Hub  #: Hub in charge of handling the Managers

    def __init__(self, game_step_override: Optional[int] = None):  # pragma: no cover
        """Load config and set up necessary attributes.

        Parameters
        ----------
        game_step_override :
            If provided, set the game_step to this value regardless of how it was
            specified elsewhere
        """
        super().__init__()
        # use this Dict when compiling
        # self.config: Dict = CONFIG
        # otherwise we use the config.yml file
        __ares_config_location__: str = path.realpath(
            path.join(getcwd(), path.dirname(__file__))
        )
        self.__user_config_location__: str = path.abspath(".")
        config_parser: ConfigParser = ConfigParser(
            __ares_config_location__, self.__user_config_location__
        )

        self.config = config_parser.parse()

        self.game_step_override: Optional[int] = game_step_override
        self.unit_tag_dict: Dict[int, Unit] = {}
        self.chat_debug = None
        self.forcefield_to_bile_dict: Dict[Point2, int] = {}
        self.last_game_loop: int = -1

        # track adept shades as we only add them towards shade completion (160 frames)
        # Key: tag of shade Value: frame shade commenced (+32 if no adept owner found)
        self.adept_shades: DefaultDict[int, Dict] = defaultdict(dict)
        self.adept_tags_with_shades_assigned: Set[int] = set()
        # we skip python-sc2 iterations in realtime, so we keep track of our own one
        self.actual_iteration: int = 0
        self.WORKER_TYPES = WORKER_TYPES | {UnitID.DRONEBURROWED}
        self.supply_type: UnitID = UnitID.OVERLORD
        self.num_larva_left: int = 0

        self._same_order_actions: list[
            tuple[AbilityId, set[int], Optional[Union[Unit, Point2]]]
        ] = []
        self._drop_unload_actions: list[tuple[int, int]] = []
        self._archon_morph_actions: list[list] = []

        self.arcade_mode: bool = False

    def give_same_action(
        self,
        order: AbilityId,
        unit_tags: Union[List[int], set[int]],
        target: Optional[Union[Point2, int]] = None,
    ) -> None:
        self._same_order_actions.append((order, unit_tags, target))

    def do_unload_container(self, container_tag: int, index: int = 0) -> None:
        self._drop_unload_actions.append((container_tag, index))

    def request_archon_morph(self, templar: list[Unit]) -> None:
        self._archon_morph_actions.append(templar)

    # noinspection PyFinal
    def _prepare_units(self):  # pragma: no cover
        """Tweak of _prepare_units to include memory units in cached distances and some
        other tracking.

        Returns
        -------

        """
        update_managers: bool = hasattr(self, "manager_hub")
        self._reset_variables()
        # there's going to be a lot of appending, so form Units at the end
        units_to_avoid_list: List[Unit] = []
        batteries_list: List[Unit] = []
        cannons_list: List[Unit] = []
        enemy_vs_ground_static_defense_list = []
        self._clear_adept_shades()

        if update_managers:
            self._reset_managers()

        index: int = 0
        for unit in self.state.observation_raw.units:
            alliance: int = unit.alliance

            unit_type: int = unit.unit_type
            # Convert these units to effects:
            # reaper grenade, parasitic bomb dummy, forcefield
            if unit_type in FakeEffectID:
                fake_unit = EffectData(unit, fake=True)
                self.state.effects.add(fake_unit)
                # our parasitic bomb that isn't attached to an enemy
                if unit_type == UnitID.PARASITICBOMBDUMMY.value:
                    if unit.alliance == 1:
                        self.friendly_parasitic_bomb_positions.append(
                            list(fake_unit.positions)[0]
                        )
                    else:
                        self.enemy_parasitic_bomb_positions.append(
                            list(fake_unit.positions)[0]
                        )
                continue

            unit_obj = Unit(
                unit,
                self,
                distance_calculation_index=index,
                base_build=self.base_build,
            )

            if unit_obj.type_id in ALL_GAS:
                self.all_gas_buildings.append(unit_obj)

            index += 1
            self.all_units.append(unit_obj)
            self.unit_tag_dict[unit_obj.tag] = unit_obj
            if unit.display_type == IS_PLACEHOLDER:
                self.placeholders.append(unit_obj)
                continue

            # Alliance.Neutral.value = 3
            if alliance == 3:
                units_to_avoid_list = self._add_neutral_unit(
                    unit_obj, unit_type, units_to_avoid_list
                )

            # Alliance.Self.value = 1
            elif alliance == 1:
                units_to_avoid_list = self._add_own_unit(
                    unit_obj, units_to_avoid_list, update_managers
                )

            # Alliance.Enemy.value = 4
            elif alliance == 4:
                if not self._should_add_unit(unit):
                    continue
                (
                    batteries_list,
                    cannons_list,
                    enemy_vs_ground_static_defense_list,
                ) = self._add_enemy_unit(
                    batteries_list,
                    cannons_list,
                    enemy_vs_ground_static_defense_list,
                    unit_obj,
                    update_managers,
                )

        self.units_to_avoid = Units(units_to_avoid_list, self)
        self.batteries = Units(batteries_list, self)
        self.cannons = Units(cannons_list, self)
        self.enemy_vs_ground_static_defense = Units(
            enemy_vs_ground_static_defense_list, self
        )
        self.num_larva_left = len(self.larva)

        if update_managers:
            self._update_memory_units(index)

        _ = self._cdist

    async def on_before_start(self) -> None:  # pragma: no cover
        """Train a drone and split workers before managers are set up

        Called before bot properly initializes

        Returns
        -------
        None
        """
        # optional build order config from a user, add to the existing config dictionary
        __user_build_orders_location__: str = path.join(
            self.__user_config_location__, f"{self.race.name.lower()}_builds.yml"
        )
        if path.isfile(__user_build_orders_location__):
            with open(__user_build_orders_location__, "r") as config_file:
                build_order_config: dict = yaml.safe_load(config_file)
                self.config.update(build_order_config)

        self.gas_type = race_gas[self.race]
        self.worker_type = race_worker[self.race]
        self.supply_type = RACE_SUPPLY[self.race]
        if self.race != Race.Zerg:
            self.base_townhall_type = (
                UnitID.COMMANDCENTER if self.race == Race.Terran else UnitID.NEXUS
            )
        else:
            self.base_townhall_type = UnitID.HATCHERY

    async def on_start(self) -> None:  # pragma: no cover
        """Set up game step, managers, and information that requires game data

        Called just before the first step, all game info is available

        Returns
        -------
        None
        """
        # manually skip the frames in realtime
        if self.realtime:
            self.client.game_step = 1
        elif self.game_step_override:
            self.client.game_step = self.game_step_override
        else:
            # set the game step from config
            self.client.game_step = (
                self.config[GAME_STEP]
                if not self.config[DEBUG]
                else self.config[DEBUG_GAME_STEP]
            )

        if not self.enemy_start_locations or not self.townhalls:
            self.arcade_mode = True

        self.register_managers()

        self.build_order_runner: BuildOrderRunner = BuildOrderRunner(
            self,
            self.manager_hub.data_manager.chosen_opening,
            self.config,
            self.manager_hub.manager_mediator,
        )
        self.behavior_executioner: BehaviorExecutioner = BehaviorExecutioner(
            self, self.config, self.manager_hub.manager_mediator
        )

        if self.config[DEBUG] and self.config[DEBUG_OPTIONS][CHAT_DEBUG]:
            from ares.chat_debug import ChatDebug

            self.chat_debug = ChatDebug(self)

        self.cost_dict: Dict[UnitID, Cost] = COST_DICT

    def register_managers(self) -> None:
        """Register standard and custom managers.

        Override in your bot class if you wish to use custom managers.

        Examples
        --------
        custom_production_manager = CustomProductionManager(
            self, self.config, manager_mediator
        )
        new_manager = NewManager(self, self.config, manager_mediator)

        self.manager_hub = Hub(
            self,
            self.config,
            manager_mediator,
            production_manager=custom_production_manager,
            additional_managers=[new_manager],
        )

        Returns
        -------
        None
        """
        manager_mediator: ManagerMediator = ManagerMediator()
        self.manager_hub = Hub(self, self.config, manager_mediator)
        self.manager_hub.init_managers()

    async def on_step(self, iteration: int) -> None:  # pragma: no cover
        """Play the game

        Called on every game step

        Parameters
        ----------
        iteration : int
            The current game iteration

        Returns
        -------
        None

        """

        """
        If playing in realtime, we set the game step to 1 (in on_start) and then
        manually skip frames. This gives Ares a time limit of 4 frames (45ms per frame)
        to finish an iteration. Playing every 4th frame seems to be the generally
        accepted solution to prevent weird things going on. And from Ares' point of
        view, they have a better chance of running smoothly on older PC's.
        """
        if self.realtime and self.last_game_loop + 4 > self.state.game_loop:
            return

        self.last_game_loop = self.state.game_loop

        await self.manager_hub.update_managers(self.actual_iteration)
        if not self.build_order_runner.build_completed:
            await self.build_order_runner.run_build()

        # detect scouts used by the build runner that are finished
        if self.time < 390.0:
            if scouts := [
                w
                for w in self.mediator.get_units_from_role(
                    role=UnitRole.BUILD_RUNNER_SCOUT, unit_type=WORKER_TYPES
                )
                if w.is_idle
            ]:
                for scout in scouts:
                    self.mediator.assign_role(tag=scout.tag, role=UnitRole.GATHERING)

        self.actual_iteration += 1
        if self.chat_debug:
            await self.chat_debug.parse_commands()

    async def _after_step(self) -> int:
        self.behavior_executioner.execute()
        for drop_action in self._drop_unload_actions:
            await self.unload_container(drop_action[0], drop_action[1])
        for same_order in self._same_order_actions:
            await self._give_units_same_order(
                same_order[0], same_order[1], same_order[2]
            )
        for archon_morph_action in self._archon_morph_actions:
            await self._do_archon_morph(archon_morph_action)
        self.manager_hub.path_manager.reset_grids(self.actual_iteration)
        await self.manager_hub.placement_manager.do_warp_ins()
        return await super(AresBot, self)._after_step()

    def register_behavior(self, behavior: Behavior) -> None:
        """Register behavior.

        Shortcut to `self.behavior_executioner.register_behavior`

        Parameters
        ----------
        behavior : Behavior
            Class that follows the Behavior interface.

        Returns
        -------
        None
        """
        self.behavior_executioner.register_behavior(behavior)

    @property
    def mediator(self) -> ManagerMediator:
        """Register behavior.

        Shortcut to `self.manager_hub.manager_mediator`


        Returns
        -------
        ManagerMediator

        """
        return self.manager_hub.manager_mediator

    async def on_end(self, game_result: Result) -> None:
        """Output game info to the log and save data (if enabled)

        Called on game end


        Parameters
        ----------
        game_result : Result
            The game result

        Returns
        -------
        None
        """
        # TODO: Put this in a method somewhere
        logger.info("END GAME REPORT")
        logger.info(f"Idle worker time: {self.state.score.idle_worker_time}")
        logger.info(f"Killed value units: {self.state.score.killed_value_units}")
        logger.info(
            f"Killed value structures: {self.state.score.killed_value_structures}"
        )
        logger.info(f"Collected minerals: {self.state.score.collected_minerals}")
        logger.info(f"Collected vespene: {self.state.score.collected_vespene}")
        if self.config[USE_DATA]:
            self.manager_hub.on_game_end(game_result)

    async def on_building_construction_complete(self, unit: Unit) -> None:
        """On structure completion event (own units)

        Parameters
        ----------
        unit :
            The Unit that just finished building

        Returns
        -------
        None
        """
        await self.manager_hub.on_structure_complete(unit)

    async def on_unit_created(self, unit: Unit) -> None:
        """On unit created event (own units)

        Parameters
        ----------
        unit :
            The Unit that was just created

        Returns
        -------
        None
        """
        if (
            not self.build_order_runner.build_completed
            and UpgradeId.WARPGATERESEARCH in self.state.upgrades
            and unit.type_id in GATEWAY_UNITS
        ):
            self.build_order_runner.set_step_started(True, unit.type_id)
        if (
            not self.build_order_runner.build_completed
            and unit.type_id == UnitID.ARCHON
        ):
            self.build_order_runner.set_step_complete(UnitID.ARCHON)
        await self.manager_hub.on_unit_created(unit)

    async def on_unit_destroyed(self, unit_tag: int) -> None:
        """On unit or structure destroyed event

        Parameters
        ----------
        unit_tag :
            The tag of the unit that was just destroyed

        Returns
        -------
        None
        """
        await self.manager_hub.on_unit_destroyed(unit_tag)

    async def on_unit_took_damage(self, unit: Unit, amount_damage_taken: float) -> None:
        """On unit or structure taking damage

        Parameters
        ----------
        unit :
            The Unit that took damage
        amount_damage_taken :
            The amount of damage the Unit took

        Returns
        -------
        None
        """
        await self.manager_hub.on_unit_took_damage(unit)

    async def on_building_construction_started(self, unit: Unit) -> None:
        """On structure starting

        Parameters
        ----------
        unit :

        Returns
        -------
        None
        """
        self.manager_hub.on_building_started(unit)
        self.build_order_runner.set_step_complete(unit.type_id)

    def _add_enemy_unit(
        self,
        batteries_list: List[Unit],
        cannons_list: List[Unit],
        enemy_vs_ground_static_defense_list: List[Unit],
        unit_obj: Unit,
        update_managers: bool,
    ) -> Tuple[List, List, List]:
        """Add a given enemy unit to the appropriate objects

        Parameters
        ----------
        batteries_list :
            Current list of enemy Shield Batteries
        cannons_list :
            Current list of enemy Photon Cannons
        enemy_vs_ground_static_defense_list :
            Current list of enemy static defense that can target ground units
        unit_obj :
            The Unit in question
        update_managers :
            Whether the Managers have been prepared

        Returns
        -------
        None

        """

        self.all_enemy_units.append(unit_obj)
        unit_id = unit_obj.type_id
        if unit_id in DETECTOR_RANGES:
            self.enemy_detectors.append(unit_obj)
        if unit_id in ALL_STRUCTURES:
            self.enemy_structures.append(unit_obj)
            if unit_id == UnitID.SHIELDBATTERY:
                batteries_list.append(unit_obj)
                if unit_obj.has_buff(BuffId.BATTERYOVERCHARGE):
                    self.overcharged_battery = unit_obj
            elif unit_id == UnitID.PHOTONCANNON:
                cannons_list.append(unit_obj)
            if unit_id in ENEMY_VS_GROUND_STATIC_DEFENSE_TYPES:
                enemy_vs_ground_static_defense_list.append(unit_obj)
            if update_managers:
                self.manager_hub.path_manager.add_structure_influence(unit_obj)
        else:
            self.enemy_units.append(unit_obj)
            if BuffId.PARASITICBOMB in unit_obj.buffs:
                self.friendly_parasitic_bomb_positions.append(unit_obj.position)
            if unit_id in self.WORKER_TYPES:
                self.enemy_workers.append(unit_obj)
            if update_managers:
                self.manager_hub.unit_cache_manager.store_enemy_unit(unit_obj)
                self.manager_hub.unit_memory_manager.store_unit(unit_obj)

        return batteries_list, cannons_list, enemy_vs_ground_static_defense_list

    def _add_neutral_unit(
        self, unit_obj: Unit, unit_type: int, units_to_avoid_list: List[Unit]
    ) -> List[Unit]:
        """Add a given neutral unit to the appropriate objects

        Parameters
        ----------
        unit_obj :
            The Unit in question
        unit_type :
            Integer corresponding to a value in the UnitTypeId enum
        units_to_avoid_list :
            List of units that block positions for buildings

        Returns
        -------
        List[Unit]
            List of units that block positions for buildings
        """
        # XELNAGATOWER = 149
        if unit_type == 149:
            self.watchtowers.append(unit_obj)
        # mineral field enums
        elif unit_type in mineral_ids:
            self.mineral_field.append(unit_obj)
            self.resources.append(unit_obj)
        # geyser enums
        elif unit_type in geyser_ids:
            self.vespene_geyser.append(unit_obj)
            self.resources.append(unit_obj)
        # all destructable rocks
        else:
            if unit_type not in IGNORE_DESTRUCTABLES:
                self.destructables.append(unit_obj)
                units_to_avoid_list.append(unit_obj)

        return units_to_avoid_list

    def _add_own_unit(
        self, unit_obj: Unit, units_to_avoid_list: List[Unit], update_managers: bool
    ) -> List[Unit]:
        """Add a given friendly unit to the appropriate objects

        Parameters
        ----------
        unit_obj :
            The Unit in question
        units_to_avoid_list :
            List of units that block positions for buildings
        update_managers :
            Whether the Managers have been prepared

        Returns
        -------
        List[Unit]
            List of units that block positions for buildings
        """
        unit_type: UnitID = unit_obj.type_id
        if update_managers:
            self.manager_hub.unit_role_manager.catch_unit(unit_obj)
            self.manager_hub.ability_tracker_manager.catch_unit(unit_obj)

        self.all_own_units.append(unit_obj)
        if unit_type in UNITS_TO_AVOID_TYPES:
            units_to_avoid_list.append(unit_obj)
        else:
            self.all_own_units_slim.append(unit_obj)

        if unit_type in ALL_STRUCTURES:
            if update_managers:
                self.manager_hub.unit_cache_manager.store_own_structure(unit_obj)
            self.structures.append(unit_obj)
            if unit_type in ADD_ONS:
                if unit_type in TECHLAB_TYPES:
                    self.techlab_tags.add(unit_obj.tag)
                else:
                    self.reactor_tags.add(unit_obj.tag)
            elif unit_type in race_townhalls[self.race]:
                self.townhalls.append(unit_obj)
                if unit_obj.is_ready:
                    self.ready_townhalls.append(unit_obj)
            elif unit_obj.vespene_contents > 0 and (
                unit_type in ALL_GAS or unit_obj.vespene_contents
            ):
                # TODO: remove "or unit_obj.vespene_contents" when a Linux client newer
                # than version 4.10.0 is released
                self.gas_buildings.append(unit_obj)
            elif unit_type in {UnitID.NYDUSCANAL, UnitID.NYDUSNETWORK}:
                self.nyduses.append(unit_obj)
        else:
            if update_managers:
                self.manager_hub.unit_cache_manager.store_own_unit(unit_obj)

            self.units.append(unit_obj)
            if unit_type in self.WORKER_TYPES:
                self.workers.append(unit_obj)
            elif unit_type == UnitID.LARVA:
                self.larva.append(unit_obj)
            elif unit_type == UnitID.EGG:
                self.eggs.append(unit_obj)
            if BuffId.PARASITICBOMB in unit_obj.buffs:
                self.enemy_parasitic_bomb_positions.append(unit_obj.position)

        return units_to_avoid_list

    def _clear_adept_shades(self) -> None:
        """Remove Adept shades if they've completed or otherwise vanished

        Returns
        -------
        None
        """
        current_frame: int = self.state.game_loop
        shade_owner_tags_to_remove: List[int] = []
        keys_to_remove: List[int] = []
        for shade_tag, item in self.adept_shades.items():
            frame_shade_started: int = item[SHADE_COMMENCED]
            adept_owner: int = item[SHADE_OWNER]
            if current_frame - frame_shade_started > SHADE_DURATION:
                keys_to_remove.append(shade_tag)
                shade_owner_tags_to_remove.append(adept_owner)

        for key in keys_to_remove:
            if key in self.adept_shades:
                self.adept_shades.pop(key)

        for owner_tag in shade_owner_tags_to_remove:
            if owner_tag in self.adept_tags_with_shades_assigned:
                self.adept_tags_with_shades_assigned.remove(owner_tag)

    def _record_shade(self, shade: RawUnit) -> None:
        """Add an Adept Shade to the tracking dictionary

        Parameters
        ----------
        shade :
            The Adept Shade to be recorded

        Returns
        -------
        None
        """
        current_frame: int = self.state.game_loop
        shade_tag: int = shade.tag
        shade_position: Point2 = Point2((shade.pos.x, shade.pos.y))
        if shade_tag not in self.adept_shades:
            close_adepts: Units = self.manager_hub.unit_memory_manager.units_in_range(
                [shade_position],
                40,
                UnitTreeQueryType.EnemyGround,
                return_as_dict=False,
            )[0].filter(
                lambda u: u.tag not in self.adept_tags_with_shades_assigned
                and u.type_id == UnitID.ADEPT
            )
            if close_adepts:
                self.adept_shades[shade_tag][SHADE_OWNER] = close_adepts.closest_to(
                    shade_position
                ).tag
                self.adept_shades[shade_tag][SHADE_COMMENCED] = current_frame
                self.adept_tags_with_shades_assigned.add(close_adepts.first.tag)
            else:
                # we can't find an owner, assume 20% complete
                self.adept_shades[shade_tag][SHADE_OWNER] = 0
                self.adept_shades[shade_tag][SHADE_COMMENCED] = current_frame - 32

    def _reset_managers(self) -> None:
        """Reset managers to prepare for a new game loop.

        Returns
        -------
        None
        """
        self.manager_hub.unit_cache_manager.clear_store_dicts()
        self.manager_hub.unit_memory_manager.clear_settings()
        self.manager_hub.unit_role_manager.get_assigned_units()

    def _reset_variables(self) -> None:
        """Reset all variables that need to be populated this loop.

        Returns
        -------
        None
        """
        # Set of enemy units detected by own sensor tower,
        # as blips have less unit information than normal visible units
        self.all_units: Units = Units([], self)
        self.units: Units = Units([], self)
        self.workers: Units = Units([], self)
        self.larva: Units = Units([], self)
        self.structures: Units = Units([], self)
        self.townhalls: Units = Units([], self)
        self.ready_townhalls: Units = Units([], self)
        self.gas_buildings: Units = Units([], self)
        self.all_own_units: Units = Units([], self)
        # don't include tumors
        self.all_own_units_slim: Units = Units([], self)
        self.enemy_units: Units = Units([], self)
        self.enemy_structures: Units = Units([], self)
        self.enemy_workers: Units = Units([], self)
        self.all_enemy_units: Units = Units([], self)
        self.resources: Units = Units([], self)
        self.destructables: Units = Units([], self)
        self.watchtowers: Units = Units([], self)
        self.mineral_field: Units = Units([], self)
        self.vespene_geyser: Units = Units([], self)
        self.placeholders: Units = Units([], self)

        # some custom stuff
        self.all_gas_buildings = Units([], self)
        self.eggs: Units = Units([], self)
        self.unit_tag_dict = {}
        self.overcharged_battery: Optional[Unit] = None
        self.nyduses = Units([], self)
        self.enemy_detectors: List[Unit] = []
        self.enemy_vs_ground_static_defense: Units = Units([], self)
        self.friendly_parasitic_bomb_positions: List[Point2] = []
        self.enemy_parasitic_bomb_positions: List[Point2] = []

        self._drop_unload_actions = []
        self._same_order_actions = []
        self._archon_morph_actions = []

    def _should_add_unit(self, unit: RawUnit) -> bool:
        """Whether the given unit should be tracked.

        This will always return True unless the unit is an Adept Shade, in which
        case whether it's added is based on frame counts.

        Parameters
        ----------
        unit :
            The unit in question

        Returns
        -------
        bool :
            True if the unit should be recorded, False otherwise
        """
        if unit.unit_type == UnitID.ADEPTPHASESHIFT.value:
            if unit.tag not in self.adept_shades:
                self._record_shade(unit)

            frame_shade_commenced: int = self.adept_shades[unit.tag][SHADE_COMMENCED]
            frame_difference: int = self.state.game_loop - frame_shade_commenced

            return frame_difference >= ADD_SHADES_ON_FRAME

        return True

    def _update_memory_units(self, index: int):
        """Go through memory units and add them to all_units.

        Parameters
        ----------
        index :
            Current distance calculation index

        Returns
        -------
        None
        """
        self.manager_hub.unit_cache_manager.update_enemy_army()

        for unit in self.manager_hub.unit_memory_manager.ghost_units.tags_not_in(
            self.all_units.tags
        ):
            unit.distance_calculation_index = index
            self.all_units.append(unit)
            self.unit_tag_dict[unit.tag] = unit
            index += 1

    def get_build_structures(
        self,
        structure_unit_types: set[UnitID],
        unit_type: UnitID,
        build_dict=None,
        ignored_build_from_tags=None,
    ) -> list[Unit]:
        """Get all structures (or units) where we can spawn unit_type.
        Takes into account techlabs and reactors. And Gateway / warp gate


        Parameters
        ----------
        structure_unit_types :
            The valid build structures we can spawn this unit_type from.
        unit_type :
            The target unit we are trying to spawn.
        build_dict : dict[Unit, UnitID] (optional)
            Use to prevent selecting idle build structures that
            have already got a pending order this frame.
            Key: Unit that should get order, value: what UnitID to build
        ignored_build_from_tags : Set[int]
            Pass in if you don't want certain build structures selected.

        Returns
        -------
        list[Unit] :
            List of structures / units where this unit could possibly be spawned from.
        """
        if ignored_build_from_tags is None:
            ignored_build_from_tags = {}
        if build_dict is None:
            build_dict = {}

        structures_dict: dict[UnitID:Units] = self.mediator.get_own_structures_dict
        own_army_dict: dict[UnitID:Units] = self.mediator.get_own_army_dict
        build_from_dict: dict[UnitID:Units] = structures_dict
        if self.race != Race.Terran:
            build_from_dict: dict[UnitID:Units] = {
                **structures_dict,
                **own_army_dict,
            }
        build_from_tags: list[int] = []
        using_larva: bool = False
        for structure_type in structure_unit_types:
            if structure_type not in build_from_dict:
                continue

            if structure_type == UnitID.LARVA:
                using_larva = True

            build_from: Union[Units, list[Unit]] = build_from_dict[structure_type]
            # only add if warpgate is off cooldown
            if structure_type == UnitID.WARPGATE:
                build_from = [
                    b
                    for b in build_from
                    if AbilityId.WARPGATETRAIN_ZEALOT in b.abilities
                ]

            requires_techlab: bool = self.race == Race.Terran and TRAIN_INFO[
                structure_type
            ][unit_type].get("requires_techlab", False)
            if not requires_techlab:
                build_from_tags.extend(
                    [
                        u.tag
                        for u in build_from
                        if u.is_ready and u.is_idle and u not in build_dict
                    ]
                )
                if self.race == Race.Terran:
                    build_from_tags.extend(
                        u.tag
                        for u in build_from
                        if u.is_ready
                        and u.has_reactor
                        and len(u.orders) < 2
                        and u not in build_dict
                    )
            else:
                build_from_tags.extend(
                    [
                        u.tag
                        for u in build_from
                        if u.is_ready
                        and u.is_idle
                        and u.has_add_on
                        and self.unit_tag_dict[u.add_on_tag].is_ready
                        and u.add_on_tag in self.techlab_tags
                        and u not in build_dict
                    ]
                )

        build_structures: list[Unit] = [self.unit_tag_dict[u] for u in build_from_tags]
        # sort build structures with reactors first
        if self.race == Race.Terran:
            build_structures = sorted(
                build_structures,
                key=lambda structure: -1 * (structure.add_on_tag in self.reactor_tags)
                + 1 * (structure.add_on_tag in self.techlab_tags),
            )
        # limit build structures to number of larva left
        if self.race == Race.Zerg and using_larva:
            build_structures = build_structures[: self.num_larva_left]
        # limit to powered structures
        if self.race == Race.Protoss:
            build_structures = [
                s
                for s in build_structures
                if s.is_powered
                or s.type_id in {UnitID.NEXUS, UnitID.DARKTEMPLAR, UnitID.HIGHTEMPLAR}
            ]

        return build_structures

    def structure_present_or_pending(self, structure_type: UnitID) -> bool:
        """
        Checks presence of a structure, or if worker is on route to
        build structure.

        Parameters
        ----------
        structure_type

        Returns
        -------
        bool

        """
        return (
            len(self.mediator.get_own_structures_dict[structure_type]) > 0
            or self.mediator.get_building_counter[structure_type] > 0
        )

    def unit_pending(self, unit_type: UnitID) -> int:
        """
        Checks pending units.
        Alternative and faster version of `self.already_pending`

        Parameters
        ----------
        unit_type

        Returns
        -------
        int

        """
        return cy_unit_pending(self, unit_type)

    def structure_pending(self, structure_type: UnitID) -> int:
        """
        Checks pending structures, includes workers on route.
        Alternative and faster version of `self.already_pending`

        Parameters
        ----------
        structure_type

        Returns
        -------
        int

        """
        num_pending: int = 0
        building_tracker: dict = self.mediator.get_building_tracker_dict
        for tag, info in building_tracker.items():
            structure_id: UnitID = building_tracker[tag][ID]
            if structure_id != structure_type:
                continue

            num_pending += 1

        if self.race != Race.Terran or structure_type in ADD_ONS:
            num_pending += len(
                [
                    s
                    for s in self.mediator.get_own_structures_dict[structure_type]
                    if s.build_progress < 1.0
                ]
            )

        return num_pending
