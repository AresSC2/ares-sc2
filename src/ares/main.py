"""Ares

The bot will be called from here, but most of the logic should be in Hub.
"""
from collections import defaultdict
from typing import DefaultDict, Dict, List, Optional, Set, Tuple

import yaml
from consts import (
    ADD_SHADES_ON_FRAME,
    ALL_STRUCTURES,
    BANNED_PHRASES,
    CHAT_DEBUG,
    CONFIG_FILE,
    DEBUG,
    DEBUG_GAME_STEP,
    DEBUG_OPTIONS,
    DEBUG_SPAWN,
    GAME_STEP,
    IGNORE_DESTRUCTABLES,
    IGNORE_IN_COST_DICT,
    SHADE_COMMENCED,
    SHADE_DURATION,
    SHADE_OWNER,
    UNITS_TO_AVOID_TYPES,
    USE_DATA,
    WORKER_TYPES,
    UnitTreeQueryType,
)
from custom_bot_ai import CustomBotAI
from dicts.enemy_detector_ranges import ENEMY_DETECTOR_RANGES
from dicts.enemy_vs_ground_static_defense_ranges import (
    ENEMY_VS_GROUND_STATIC_DEFENSE_TYPES,
)
from dicts.unit_data import UNIT_DATA
from loguru import logger
from managers.hub import Hub
from s2clientprotocol.raw_pb2 import Unit as RawUnit
from sc2.constants import ALL_GAS, IS_PLACEHOLDER, FakeEffectID, geyser_ids, mineral_ids
from sc2.data import Race, Result, race_gas, race_townhalls, race_worker
from sc2.game_data import Cost
from sc2.game_state import EffectData
from sc2.ids.buff_id import BuffId
from sc2.ids.unit_typeid import UnitTypeId as UnitID
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units


class AresBot(CustomBotAI):
    """Final setup of CustomBotAI for usage.

    Most bot logic should go in Hub.
    """

    cost_dict: Dict[UnitID, Cost]  #: UnitTypeId to cost for faster lookup later
    manager_hub: Hub  #: Hub in charge of handling the Managers

    def __init__(self, game_step_override: Optional[int] = None):
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
        # otherwise we use the config.yaml file
        with open(CONFIG_FILE, "r") as config_file:
            self.config = yaml.safe_load(config_file)

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

    # noinspection PyFinal
    def _prepare_units(self):
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

        if update_managers:
            self._update_memory_units(index)

        # Force distance calculation and caching on all units using scipy pdist or cdist
        # TODO: Check which one is actually faster,
        #   it's always set to 2 currently so no need to keep checking the if/elif
        _ = self._cdist
        # if self.distance_calculation_method == 1:
        #     _ = self._pdist
        # elif self.distance_calculation_method in {2, 3}:
        #     _ = self._cdist

    async def on_before_start(self) -> None:
        """Train a drone and split workers before managers are set up

        Called before bot properly initializes

        Returns
        -------

        """
        self.gas_type = race_gas[self.race]
        self.worker_type = race_worker[self.race]
        if self.race != Race.Zerg:
            self.townhalls.first.train(self.worker_type)
            self.base_townhall_type = (
                UnitID.COMMANDCENTER if self.race == Race.Terran else UnitID.NEXUS
            )
        else:
            self.base_townhall_type = UnitID.HATCHERY
            self.larva.first.train(UnitID.DRONE)
        for worker in self.workers:
            worker.gather(self.mineral_field.closest_to(worker))

    async def on_start(self) -> None:
        """Set up game step, managers, and information that requires game data

        Called just before the first step, all game info is available

        Returns
        -------

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

        self.manager_hub = Hub(self, self.config)
        await self.manager_hub.init_managers()

        if self.config[DEBUG] and self.config[DEBUG_OPTIONS][CHAT_DEBUG]:
            from chat_debug import ChatDebug

            self.chat_debug = ChatDebug(self)

        if self.config[DEBUG] and self.config[DEBUG_OPTIONS][DEBUG_SPAWN]:
            from debug_spawn import DebugSpawn

            debug_spawn: DebugSpawn = DebugSpawn(self)
            await debug_spawn.spawn(
                self.manager_hub.terrain_manager.enemy_nat,
                self.manager_hub.terrain_manager.own_nat,
                self.manager_hub.terrain_manager.enemy_third,
            )
        self.cost_dict: Dict[UnitID, Cost] = {
            unit_id: self.calculate_cost(unit_id)
            for unit_id in UNIT_DATA
            if (
                unit_id not in IGNORE_IN_COST_DICT
                and not any(
                    [banned_phrase in unit_id.name for banned_phrase in BANNED_PHRASES]
                )
            )
        }

    async def on_step(self, iteration: int) -> None:
        """Play the game

        Called on every game step

        Parameters
        ----------
        iteration : int
            The current game iteration

        Returns
        -------

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
        self.actual_iteration += 1
        if self.chat_debug:
            await self.chat_debug.parse_commands()

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

        """
        await self.manager_hub.on_unit_created(unit)

    async def on_unit_destroyed(self, unit_tag: int) -> None:
        """On unit or structure destroyed event

        Parameters
        ----------
        unit_tag :
            The tag of the unit that was just destroyed

        Returns
        -------

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

        """
        await self.manager_hub.on_unit_took_damage(unit)

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

        """

        self.all_enemy_units.append(unit_obj)
        unit_id = unit_obj.type_id
        if unit_id in ENEMY_DETECTOR_RANGES:
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
            self.manager_hub.ability_tracker_manager.catch_unit(unit_obj, unit_type)

        self.all_own_units.append(unit_obj)
        if unit_type in UNITS_TO_AVOID_TYPES:
            units_to_avoid_list.append(unit_obj)
        if unit_type in ALL_STRUCTURES:
            if update_managers:
                self.manager_hub.unit_cache_manager.store_own_structure(unit_obj)
            self.structures.append(unit_obj)
            if unit_type in race_townhalls[self.race]:
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

        """
        self.manager_hub.unit_cache_manager.clear_store_dicts()
        self.manager_hub.unit_memory_manager.clear_settings()
        self.manager_hub.unit_role_manager.get_assigned_units()

    def _reset_variables(self) -> None:
        """Reset all variables that need to be populated this loop.

        Returns
        -------

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

        """
        self.manager_hub.unit_cache_manager.update_enemy_army()

        for unit in self.manager_hub.unit_memory_manager.ghost_units.tags_not_in(
            self.all_units.tags
        ):
            unit.distance_calculation_index = index
            self.all_units.append(unit)
            self.unit_tag_dict[unit.tag] = unit
            index += 1
