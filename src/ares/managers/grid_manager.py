"""Handle grid information and influence.

This manager handles all grid-related operations including initialization,
cost calculations, and influence management.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List

import numpy as np
from cython_extensions import cy_distance_to_squared
from map_analyzer import MapData
from sc2.data import Race
from sc2.ids.effect_id import EffectId
from sc2.ids.unit_typeid import UnitTypeId as UnitID
from sc2.position import Point2, Point3
from sc2.unit import Unit
from sc2.units import Units

from ares.consts import (
    ACTIVE_GRID,
    AIR,
    AIR_AVOIDANCE,
    AIR_COST,
    AIR_RANGE,
    AIR_VS_GROUND,
    AIR_VS_GROUND_DEFAULT,
    BLINDING_CLOUD,
    CHANGELING_TYPES,
    CORROSIVE_BILE,
    COST,
    COST_MULTIPLIER,
    DEBUG,
    DEBUG_OPTIONS,
    EFFECTS,
    EFFECTS_RANGE_BUFFER,
    FEATURES,
    GROUND,
    GROUND_AVOIDANCE,
    GROUND_COST,
    GROUND_RANGE,
    GROUND_TO_AIR,
    KD8_CHARGE,
    LIBERATOR_ZONE,
    LURKER_SPINE,
    NUKE,
    ORACLE,
    PARASITIC_BOMB,
    PATHING,
    RANGE,
    RANGE_BUFFER,
    SHOW_PATHING_COST,
    STORM,
    TACTICAL_GROUND,
    TACTICAL_GROUND_GRID,
    TOWNHALL_TYPES,
    UNITS,
    ManagerName,
    ManagerRequestType,
)
from ares.dicts.unit_data import UNIT_DATA
from ares.dicts.weight_costs import WEIGHT_COSTS
from ares.managers.manager import Manager
from ares.managers.manager_mediator import IManagerMediator, ManagerMediator

if TYPE_CHECKING:
    from ares import AresBot


class GridManager(Manager, IManagerMediator):
    """Manager for handling grids.

    This manager handles all grid-related operations including initialization,
    cost calculations, and influence management.
    """

    BILE_DURATION: int = 50
    REACT_TO_BILES_ON_FRAME: int = 16
    FORCEFIELD: str = "FORCEFIELD"
    NUKE_DURATION: int = 320
    REACT_TO_NUKES_ON_FRAME: int = 250
    NOVA_RADIUS: float = 1.5

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
            The result of the request
        """
        return self.manager_requests_dict[request](kwargs)

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
        """
        super().__init__(ai, config, mediator)
        self.debug: bool = self.config[DEBUG]
        self.map_data: MapData = MapData(ai, arcade=self.ai.arcade_mode)

        self.manager_requests_dict = {
            ManagerRequestType.GET_AIR_AVOIDANCE_GRID: (
                lambda kwargs: self.air_avoidance_grid
            ),
            ManagerRequestType.GET_AIR_GRID: (lambda kwargs: self.air_grid),
            ManagerRequestType.GET_AIR_VS_GROUND_GRID: (
                lambda kwargs: self.air_vs_ground_grid
            ),
            ManagerRequestType.GET_CACHED_GROUND_GRID: (
                lambda kwargs: self._cached_clean_ground_grid
            ),
            ManagerRequestType.GET_CLIMBER_GRID: (lambda kwargs: self.climber_grid),
            ManagerRequestType.GET_FORCEFIELD_POSITIONS: (
                lambda kwargs: self.forcefield_positions
            ),
            ManagerRequestType.GET_GROUND_AVOIDANCE_GRID: (
                lambda kwargs: self.ground_avoidance_grid
            ),
            ManagerRequestType.GET_GROUND_GRID: (lambda kwargs: self.ground_grid),
            ManagerRequestType.GET_GROUND_TO_AIR_GRID: (
                lambda kwargs: self.ground_to_air_grid
            ),
            ManagerRequestType.GET_MAP_DATA: (lambda kwargs: self.map_data),
            ManagerRequestType.GET_PRIORITY_GROUND_AVOIDANCE_GRID: (
                lambda kwargs: self.priority_ground_avoidance_grid
            ),
            ManagerRequestType.GET_TACTICAL_GROUND_GRID: (
                lambda kwargs: self.tactical_ground_grid
            ),
        }

        self.air_grid: np.ndarray = self.map_data.get_clean_air_grid()
        # grid where ground pathable tiles have influence so flyers avoid
        self.air_vs_ground_grid: np.ndarray = self.map_data.get_air_vs_ground_grid(
            default_weight=AIR_VS_GROUND_DEFAULT
        )
        self.climber_grid: np.ndarray = self.map_data.get_climber_grid()
        self.ground_grid: np.ndarray = self.map_data.get_pyastar_grid()
        # tiles without creep are listed as unpathable
        self.creep_ground_grid: np.ndarray = self.map_data.get_pyastar_grid()
        # this is like the air grid above,
        # but only add influence from enemy ground
        self.ground_to_air_grid: np.ndarray = self.air_grid.copy()

        self._cached_clean_air_grid: np.ndarray = self.air_grid.copy()
        self._cached_clean_air_vs_ground_grid: np.ndarray = (
            self.air_vs_ground_grid.copy()
        )

        self._cached_clean_ground_grid: np.ndarray = self.ground_grid.copy()
        self._cached_climber_grid: np.ndarray = self.climber_grid.copy()
        # avoidance grids will contain influence for things our units should avoid
        self.air_avoidance_grid: np.ndarray = self._cached_clean_air_grid.copy()
        self.ground_avoidance_grid: np.ndarray = self._cached_clean_ground_grid.copy()
        # certain things ground units should always avoid
        self.priority_ground_avoidance_grid: np.ndarray = (
            self._cached_clean_ground_grid.copy()
        )

        self.tactical_ground_grid_enabled: bool = self.config[FEATURES][
            TACTICAL_GROUND_GRID
        ]
        # ensure grid exists so mediator request dont break
        self.tactical_ground_grid: np.ndarray = self.map_data.get_pyastar_grid(
            default_weight=200
        )

        self.forcefield_positions: List[Point2] = []
        # biles / nukes
        self.delayed_effects: Dict[int, int] = {}

        # track biles, since they disappear from the observation right before they land
        # key is position, value is the frame the bile was first seen (50 frames total)
        self.biles_dict: Dict[Point2, int] = dict()
        self.storms_dict: Dict[Point2, int] = dict()

    async def update(self, iteration: int) -> None:
        """Keep track of everything.

        Parameters
        ----------
        iteration :
            The game iteration.
        """
        self.forcefield_positions = []
        self._add_effects()

        # nukes / biles
        self._update_delayed_effects()

        for unit in self.ai.enemy_units:
            if unit.type_id not in CHANGELING_TYPES:
                self.add_unit_influence(unit)

        unit_data: dict = UNIT_DATA
        if self.tactical_ground_grid_enabled:
            # avoid looping over hundreds of tumors as zerg
            units_collection: Units = self.ai.units if self.ai.race == Race.Zerg else self.ai.all_own_units
            for unit in units_collection:
                type_id: UnitID = unit.type_id
                if type_id == UnitID.DISRUPTOR:
                    continue
                data: dict = unit_data[type_id]
                if not data["flying"]:
                    influence: float = data["army_value"]
                    if unit.health <= 100.0:
                        influence *= 1.5

                    self.tactical_ground_grid = self.map_data.add_cost(
                        position=unit.position,
                        radius=unit.radius + self.NOVA_RADIUS,
                        grid=self.tactical_ground_grid,
                        weight=-influence
                    )

        # update creep grid
        self.creep_ground_grid = self.ground_grid.copy()
        self.creep_ground_grid[np.where(self.ai.state.creep.data_numpy.T != 1)] = np.inf

        if self.debug and self.config[DEBUG_OPTIONS][SHOW_PATHING_COST]:
            debug_cases: dict[str, Any] = {
                AIR: (self.air_grid, 1),
                AIR_VS_GROUND: (self.air_vs_ground_grid, 40),
                GROUND: (self.ground_grid, 1),
                GROUND_AVOIDANCE: (self.ground_avoidance_grid, 1),
                AIR_AVOIDANCE: (self.air_avoidance_grid, 1),
                GROUND_TO_AIR: (self.ground_to_air_grid, 1),
                TACTICAL_GROUND: (self.tactical_ground_grid, 200),
            }

            for option, (grid, threshold) in debug_cases.items():
                if self.config[DEBUG_OPTIONS][ACTIVE_GRID] == option:
                    if option == TACTICAL_GROUND:
                        height: float = self.ai.get_terrain_z_height(
                            self.ai.start_location
                        )
                        indices = np.where(grid != threshold)
                        for x, y in zip(
                            indices[0], indices[1]
                        ):  # Properly zip the x and y coordinates
                            pos: Point3 = Point3((x, y, height))
                            if grid[x, y] == np.inf:
                                val: int = 9999
                            else:
                                val: int = int(grid[x, y])
                            if val != 9999:
                                self.ai.client.debug_text_world(
                                    str(val), pos, (201, 168, 79), 13
                                )
                    else:
                        self.map_data.draw_influence_in_game(
                            grid, lower_threshold=threshold
                        )
                    break

    def add_cost(
        self,
        pos: Point2,
        weight: float,
        unit_range: float,
        grid: np.ndarray,
        initial_default_weights: int = 0,
    ) -> np.ndarray:
        """Add values to a grid.

        Costs can also be considered "influence", mostly used to add enemies to a grid.

        Parameters
        ----------
        pos :
            Where the cause of the increased cost is located.
        weight :
            How much the cost should change by.
        unit_range :
            Radius of a circle centered at pos that contains all points that the cost
            should be added to.
        grid :
            Which pathing grid to increase the costs of.
        initial_default_weights :
            Default value of the grid being added to.

        Returns
        -------
        np.ndarray :
            The updated grid.
        """
        grid = self.map_data.add_cost(
            position=(int(pos.x), int(pos.y)),
            radius=unit_range,
            grid=grid,
            weight=int(weight) * self.config[PATHING][COST_MULTIPLIER],
            initial_default_weights=initial_default_weights,
        )
        return grid

    def add_cost_to_multiple_grids(
        self,
        pos: Point2,
        weight: float,
        unit_range: float,
        grids: List[np.ndarray],
        initial_default_weights: int = 0,
    ) -> List[np.ndarray]:
        """Add values to multiple grids at once.

        Costs can also be considered "influence", mostly used to add enemies to a grid.

        Parameters
        ----------
        pos :
            Where the cause of the increased cost is located.
        weight :
            How much the cost should change by.
        unit_range :
            Radius of a circle centered at pos that contains all points that the cost
            should be added to.
        grids :
            Which pathing grids to increase the costs of.
        initial_default_weights :
            Default value of the grid being added to.

        Returns
        -------
        List[np.ndarray] :
            The updated grids.
        """
        return self.map_data.add_cost_to_multiple_grids(
            position=(int(pos.x), int(pos.y)),
            radius=unit_range,
            grids=grids,
            weight=int(weight) * self.config[PATHING][COST_MULTIPLIER],
            initial_default_weights=initial_default_weights,
        )

    def reset_grids(self, iteration: int) -> None:
        """Get fresh grids so that the influence can be updated.

        Parameters
        ----------
        iteration :
            The current game iteration.
        """
        self.air_grid = self._cached_clean_air_grid.copy()
        self.air_vs_ground_grid = self._cached_clean_air_vs_ground_grid.copy()
        self.climber_grid = self._cached_climber_grid.copy()
        self.ground_grid = self._cached_clean_ground_grid.copy()
        self.air_avoidance_grid = self._cached_clean_air_grid.copy()
        self.ground_avoidance_grid = self._cached_clean_ground_grid.copy()
        self.priority_ground_avoidance_grid = self._cached_clean_ground_grid.copy()
        self.ground_to_air_grid = self._cached_clean_air_grid.copy()
        if self.tactical_ground_grid_enabled:
            self.tactical_ground_grid = self.map_data.get_pyastar_grid(
                default_weight=200
            )

        # Refresh the cached ground grid every 8 steps, because things like structures/
        # minerals / rocks will change throughout the game
        # TODO: Detect changes in structures / rocks / min field, then update?
        #   Only if this is faster then updating the grid!
        if iteration % 8 == 0:
            self._cached_clean_ground_grid = self.map_data.get_pyastar_grid()
            self._cached_climber_grid = self.map_data.get_climber_grid()

    def add_unit_influence(self, enemy: Unit) -> None:
        """Add influence to the relevant grid.

        Called from _prepare_units.

        Parameters
        ----------
        enemy :
            The enemy unit to add the influence of.
        """
        if not enemy.is_ready and not enemy.is_cloaked and not enemy.is_burrowed:
            return
        self._add_unit_influence(enemy)

    def add_structure_influence(self, enemy: Unit) -> None:
        """Add structure influence to the relevant grid.

        Called from _prepare_units.

        Parameters
        ----------
        enemy :
            The enemy structure to add the influence of.
        """
        # these will expire out of our vision, don't add to grid
        if enemy.type_id == UnitID.AUTOTURRET and enemy.is_snapshot:
            return
        if enemy.is_ready:
            self._add_structure_influence(enemy)

    def _add_effects(self) -> None:
        """Add effects influence to map."""
        effect_values: Dict = self.config[PATHING][EFFECTS]
        effects_buffer = self.config[PATHING][EFFECTS_RANGE_BUFFER]

        self._process_game_effects(effect_values, effects_buffer)
        self._process_parasitic_bombs(effect_values, effects_buffer)

    def _process_game_effects(self, effect_values: Dict, effects_buffer: float) -> None:
        """Process all game effects and add their influence."""
        effect_handlers = {
            EffectId.BLINDINGCLOUDCP: self._handle_blinding_cloud,
            "KD8CHARGE": self._handle_kd8_charge,
            EffectId.LURKERMP: self._handle_lurker_spines,
            EffectId.NUKEPERSISTENT: self._handle_nuke,
            EffectId.PSISTORMPERSISTENT: self._handle_storm,
            EffectId.RAVAGERCORROSIVEBILECP: self._handle_corrosive_bile,
            self.FORCEFIELD: self._handle_forcefield,
        }

        liberator_effects = {
            EffectId.LIBERATORTARGETMORPHDELAYPERSISTENT,
            EffectId.LIBERATORTARGETMORPHPERSISTENT,
        }

        for effect in self.ai.state.effects:
            if effect.id in liberator_effects:
                self._handle_liberator_siege(effect, effect_values, effects_buffer)
            elif effect.id in effect_handlers:
                effect_handlers[effect.id](effect, effect_values, effects_buffer)

    def _process_parasitic_bombs(
        self, effect_values: Dict, effects_buffer: float
    ) -> None:
        """Process parasitic bomb effects."""
        for position in self.ai.enemy_parasitic_bomb_positions:
            self._handle_parasitic_bomb(position, effect_values, effects_buffer)

    def _handle_blinding_cloud(
        self, effect, effect_values: Dict, effects_buffer: float
    ) -> None:
        """Handle blinding cloud effect."""
        grids = [
            self.climber_grid,
            self.ground_grid,
            self.ground_avoidance_grid,
        ]
        self.add_cost_to_multiple_grids(
            Point2.center(effect.positions),
            effect_values[BLINDING_CLOUD][COST],
            effect_values[BLINDING_CLOUD][RANGE] + effects_buffer,
            grids,
        )

    def _handle_kd8_charge(
        self, effect, effect_values: Dict, effects_buffer: float
    ) -> None:
        """Handle KD8 charge effect."""
        grids = [self.climber_grid, self.ground_grid]
        self.add_cost_to_multiple_grids(
            Point2.center(effect.positions),
            effect_values[KD8_CHARGE][COST],
            effect_values[KD8_CHARGE][RANGE] + effects_buffer,
            grids,
        )

    def _handle_liberator_siege(
        self, effect, effect_values: Dict, effects_buffer: float
    ) -> None:
        """Handle liberator siege effect."""
        grids = [self.climber_grid, self.ground_grid]
        self.add_cost_to_multiple_grids(
            Point2.center(effect.positions),
            effect_values[LIBERATOR_ZONE][COST],
            effect_values[LIBERATOR_ZONE][RANGE] + effects_buffer,
            grids,
        )

    def _handle_lurker_spines(
        self, effect, effect_values: Dict, effects_buffer: float
    ) -> None:
        """Handle lurker spines effect."""
        grids = [
            self.climber_grid,
            self.ground_grid,
            self.ground_avoidance_grid,
        ]
        for pos in effect.positions:
            self.add_cost_to_multiple_grids(
                pos,
                effect_values[LURKER_SPINE][COST],
                effect_values[LURKER_SPINE][RANGE] + effects_buffer,
                grids,
            )

    def _handle_nuke(self, effect, effect_values: Dict, effects_buffer: float) -> None:
        """Handle nuke effect."""
        self._add_delayed_effect(
            position=Point2.center(effect.positions),
            effect_dict=self.storms_dict,
        )

    def _handle_storm(self, effect, effect_values: Dict, effects_buffer: float) -> None:
        """Handle psi storm effect."""
        grids = [
            self.air_grid,
            self.air_vs_ground_grid,
            self.climber_grid,
            self.ground_grid,
            self.air_avoidance_grid,
            self.ground_avoidance_grid,
            self.priority_ground_avoidance_grid,
        ]
        self.add_cost_to_multiple_grids(
            Point2.center(effect.positions),
            effect_values[STORM][COST],
            effect_values[STORM][RANGE] + effects_buffer,
            grids,
        )

    def _handle_corrosive_bile(
        self, effect, effect_values: Dict, effects_buffer: float
    ) -> None:
        """Handle corrosive bile effect."""
        self._add_delayed_effect(
            position=Point2.center(effect.positions),
            effect_dict=self.biles_dict,
        )

    def _handle_forcefield(
        self, effect, effect_values: Dict, effects_buffer: float
    ) -> None:
        """Handle forcefield effect."""
        self.forcefield_positions.append(effect.positions.pop())

    def _handle_parasitic_bomb(
        self,
        position: Point2,
        effect_values: Dict,
        effects_buffer: float,
    ) -> None:
        """Handle parasitic bomb effect."""
        grids = [
            self.air_grid,
            self.air_vs_ground_grid,
            self.air_avoidance_grid,
            self.ground_to_air_grid,
        ]
        bomb_range = effect_values[PARASITIC_BOMB][RANGE] + effects_buffer
        self.add_cost_to_multiple_grids(
            position,
            effect_values[PARASITIC_BOMB][COST],
            bomb_range,
            grids,
        )

    def _add_structure_influence(self, structure: Unit) -> None:
        """Add structure influence to map.

        Parameters
        ----------
        structure :
            The structure to add the influence of.
        """
        structure_handlers = {
            UnitID.PHOTONCANNON: self._handle_photon_cannon,
            UnitID.MISSILETURRET: self._handle_missile_turret,
            UnitID.SPORECRAWLER: self._handle_spore_crawler,
            UnitID.BUNKER: self._handle_bunker,
            UnitID.PLANETARYFORTRESS: self._handle_planetary_fortress,
            UnitID.AUTOTURRET: self._handle_auto_turret,
        }

        if structure.type_id in structure_handlers:
            structure_handlers[structure.type_id](structure)
            if self.tactical_ground_grid_enabled:
                unit_data: dict = UNIT_DATA[structure.type_id]
                if not unit_data["flying"]:
                    influence: float = unit_data["army_value"]
                    if structure.health <= 100.0:
                        influence *= 1.5
                    self.tactical_ground_grid = self.map_data.add_cost(
                        position=structure.position,
                        radius=structure.radius + self.NOVA_RADIUS,
                        grid=self.tactical_ground_grid,
                        weight=influence,
                    )

    def _handle_photon_cannon(self, structure: Unit) -> None:
        """Handle photon cannon influence."""
        grids = [
            self.air_grid,
            self.air_vs_ground_grid,
            self.climber_grid,
            self.ground_grid,
            self.ground_to_air_grid,
        ]
        self.add_cost_to_multiple_grids(
            structure.position,
            22,
            7 + self.config[PATHING][RANGE_BUFFER],
            grids,
        )

    def _handle_missile_turret(self, structure: Unit) -> None:
        """Handle missile turret influence."""
        s_range = 8 if self.ai.time > 540 else 7
        grids = [
            self.air_grid,
            self.air_vs_ground_grid,
            self.ground_to_air_grid,
        ]
        self.add_cost_to_multiple_grids(
            structure.position,
            39,
            s_range + self.config[PATHING][RANGE_BUFFER],
            grids,
        )

    def _handle_spore_crawler(self, structure: Unit) -> None:
        """Handle spore crawler influence."""
        grids = [
            self.air_grid,
            self.air_vs_ground_grid,
            self.ground_to_air_grid,
        ]
        self.add_cost_to_multiple_grids(
            structure.position,
            39,
            7 + self.config[PATHING][RANGE_BUFFER],
            grids,
        )

    def _handle_bunker(self, structure: Unit) -> None:
        """Handle bunker influence."""
        if self.ai.enemy_structures.filter(
            lambda g: g.type_id in TOWNHALL_TYPES
            and cy_distance_to_squared(g.position, structure.position) < 81.0
        ):
            return

        grids = [
            self.air_grid,
            self.air_vs_ground_grid,
            self.climber_grid,
            self.ground_grid,
            self.ground_to_air_grid,
        ]
        self.add_cost_to_multiple_grids(
            structure.position,
            22,
            6 + self.config[PATHING][RANGE_BUFFER],
            grids,
        )
        if self.tactical_ground_grid_enabled:
            self.tactical_ground_grid = self.map_data.add_cost(
                position=structure.position,
                radius=structure.radius + self.NOVA_RADIUS,
                grid=self.tactical_ground_grid,
                weight=10.0 if structure.health > 100 else 15.0,
            )

    def _handle_planetary_fortress(self, structure: Unit) -> None:
        """Handle planetary fortress influence."""
        s_range = 7 if self.ai.time > 400 else 6
        grids = [self.climber_grid, self.ground_grid]
        self.add_cost_to_multiple_grids(
            structure.position,
            28,
            s_range + self.config[PATHING][RANGE_BUFFER],
            grids,
        )
        if self.tactical_ground_grid_enabled:
            self.tactical_ground_grid = self.map_data.add_cost(
                position=structure.position,
                radius=structure.radius + self.NOVA_RADIUS,
                grid=self.tactical_ground_grid,
                weight=25.0 if structure.health < 100 else 40.0,
            )

    def _handle_auto_turret(self, structure: Unit) -> None:
        """Handle auto turret influence."""
        self._add_cost_to_all_grids(structure, WEIGHT_COSTS[UnitID.AUTOTURRET])

    def _add_unit_influence(self, unit: Unit) -> None:
        """Add unit influence to maps.

        Parameters
        ----------
        unit :
            The unit to add the influence of.
        """
        unit_handlers = {
            UnitID.DISRUPTORPHASED: self._handle_disruptor,
            UnitID.BANELING: self._handle_baneling,
            UnitID.INFESTOR: self._handle_infestor,
            UnitID.ORACLE: self._handle_oracle,
        }

        if unit.type_id in WEIGHT_COSTS:
            self._handle_weight_cost_unit(unit)
        elif unit.type_id in unit_handlers:
            unit_handlers[unit.type_id](unit)
        else:
            self._handle_generic_unit(unit)

        if self.tactical_ground_grid_enabled:
            unit_data: dict = UNIT_DATA[unit.type_id]
            if not unit_data["flying"]:
                influence: float = unit_data["army_value"]
                if unit.health <= 100.0:
                    influence *= 1.5
                self.tactical_ground_grid = self.map_data.add_cost(
                    position=unit.position,
                    radius=unit.radius + self.NOVA_RADIUS,
                    grid=self.tactical_ground_grid,
                    weight=influence,
                )

    def _handle_weight_cost_unit(self, unit: Unit) -> None:
        """Handle units with predefined weight costs."""
        weight_values = WEIGHT_COSTS[unit.type_id]
        self._add_cost_to_all_grids(unit, weight_values)
        if not unit.is_flying:
            self.ground_to_air_grid = self.map_data.add_cost(
                unit.position,
                weight_values[AIR_RANGE] + self.config[PATHING][RANGE_BUFFER],
                self.ground_to_air_grid,
                weight_values[AIR_COST],
            )

    def _handle_disruptor(self, unit: Unit) -> None:
        """Handle disruptor unit influence."""
        grids = [
            self.climber_grid,
            self.ground_avoidance_grid,
            self.ground_grid,
            self.priority_ground_avoidance_grid,
        ]
        self.add_cost_to_multiple_grids(
            pos=unit.position,
            weight=1000,
            unit_range=8 + self.config[PATHING][EFFECTS_RANGE_BUFFER],
            grids=grids,
        )

    def _handle_baneling(self, unit: Unit) -> None:
        """Handle baneling unit influence."""
        grids = [
            self.climber_grid,
            self.ground_avoidance_grid,
            self.ground_grid,
            self.priority_ground_avoidance_grid,
        ]
        self.add_cost_to_multiple_grids(
            pos=unit.position,
            weight=WEIGHT_COSTS[UnitID.BANELING][GROUND_COST],
            unit_range=WEIGHT_COSTS[UnitID.BANELING][GROUND_RANGE],
            grids=grids,
        )

    def _handle_infestor(self, unit: Unit) -> None:
        """Handle infestor unit influence."""
        if unit.energy >= 75:  # Has enough energy for fungal growth
            weight_values = WEIGHT_COSTS[UnitID.INFESTOR]
            self._add_cost_to_all_grids(unit, weight_values)
            self.ground_to_air_grid = self.map_data.add_cost(
                unit.position,
                weight_values[AIR_RANGE] + self.config[PATHING][RANGE_BUFFER],
                self.ground_to_air_grid,
                weight_values[AIR_COST],
            )

    def _handle_oracle(self, unit: Unit) -> None:
        """Handle oracle unit influence."""
        if unit.energy >= 25:  # Has enough energy for attack
            oracle_range = (
                self.config[PATHING][UNITS][ORACLE][GROUND_RANGE]
                + self.config[PATHING][RANGE_BUFFER]
            )
            grids = [self.climber_grid, self.ground_grid]
            self.add_cost_to_multiple_grids(
                unit.position,
                self.config[PATHING][UNITS][ORACLE][GROUND_COST],
                oracle_range,
                grids,
            )

    def _handle_generic_unit(self, unit: Unit) -> None:
        """Handle generic unit influence based on its capabilities."""
        if unit.ground_range < 2:  # Melee units
            self._handle_melee_unit(unit)
        else:
            if unit.can_attack_air:
                self._handle_anti_air_unit(unit)
            if unit.can_attack_ground:
                self._handle_ground_attack_unit(unit)

    def _handle_melee_unit(self, unit: Unit) -> None:
        """Handle melee unit influence."""
        self.climber_grid, self.ground_grid = self.add_cost_to_multiple_grids(
            unit.position,
            unit.ground_dps,
            self.config[PATHING][RANGE_BUFFER],
            [self.climber_grid, self.ground_grid],
        )

    def _handle_anti_air_unit(self, unit: Unit) -> None:
        """Handle anti-air unit influence."""
        self.air_grid, self.air_vs_ground_grid = self.add_cost_to_multiple_grids(
            unit.position,
            unit.air_dps,
            unit.air_range + self.config[PATHING][RANGE_BUFFER],
            [self.air_grid, self.air_vs_ground_grid],
        )
        if not unit.is_flying:
            self.ground_to_air_grid = self.map_data.add_cost(
                unit.position,
                unit.air_range + self.config[PATHING][RANGE_BUFFER],
                self.ground_to_air_grid,
                unit.air_dps,
            )

    def _handle_ground_attack_unit(self, unit: Unit) -> None:
        """Handle ground attack unit influence."""
        self.climber_grid, self.ground_grid = self.add_cost_to_multiple_grids(
            unit.position,
            unit.ground_dps,
            unit.ground_range + self.config[PATHING][RANGE_BUFFER],
            [self.climber_grid, self.ground_grid],
        )

    def _add_cost_to_all_grids(self, unit: Unit, weight_values: dict) -> None:
        """Add cost to all grids.

        Parameters
        ----------
        unit :
            Unit to add the costs of.
        weight_values :
            Dictionary containing the weights of units.
        """
        if unit.type_id == UnitID.AUTOTURRET:
            (
                self.air_grid,
                self.air_vs_ground_grid,
                self.climber_grid,
                self.ground_grid,
                self.ground_avoidance_grid,
                self.air_avoidance_grid,
                self.ground_to_air_grid,
            ) = self.add_cost_to_multiple_grids(
                unit.position,
                weight_values[AIR_COST],
                weight_values[AIR_RANGE] + self.config[PATHING][RANGE_BUFFER],
                [
                    self.air_grid,
                    self.air_vs_ground_grid,
                    self.climber_grid,
                    self.ground_grid,
                    self.ground_avoidance_grid,
                    self.air_avoidance_grid,
                    self.ground_to_air_grid,
                ],
            )

        # values are identical for air and ground, add costs to all grids at same time
        elif (
            weight_values[AIR_COST] == weight_values[GROUND_COST]
            and weight_values[AIR_RANGE] == weight_values[GROUND_RANGE]
        ):
            (
                self.air_grid,
                self.air_vs_ground_grid,
                self.climber_grid,
                self.ground_grid,
            ) = self.add_cost_to_multiple_grids(
                unit.position,
                weight_values[AIR_COST],
                weight_values[AIR_RANGE] + self.config[PATHING][RANGE_BUFFER],
                [
                    self.air_grid,
                    self.air_vs_ground_grid,
                    self.climber_grid,
                    self.ground_grid,
                ],
            )
        # ground values are different, so add cost separately
        else:
            if weight_values[AIR_RANGE] > 0:
                (
                    self.air_grid,
                    self.air_vs_ground_grid,
                ) = self.add_cost_to_multiple_grids(
                    unit.position,
                    weight_values[AIR_COST],
                    weight_values[AIR_RANGE] + self.config[PATHING][RANGE_BUFFER],
                    [self.air_grid, self.air_vs_ground_grid],
                )
            if weight_values[GROUND_RANGE] > 0:
                (
                    self.climber_grid,
                    self.ground_grid,
                ) = self.add_cost_to_multiple_grids(
                    unit.position,
                    weight_values[GROUND_COST],
                    weight_values[GROUND_RANGE] + self.config[PATHING][RANGE_BUFFER],
                    [self.climber_grid, self.ground_grid],
                )

    def _add_delayed_effect(
        self,
        position: Point2,
        effect_dict: dict,
    ) -> None:
        """Add an effect that we know exists but is not in the game observation.

        Parameters
        ----------
        position :
            Where to add the effect.
        effect_dict :
            Currently tracked effects.
        """
        # no record of this yet
        if position not in effect_dict:
            effect_dict[position] = self.ai.state.game_loop

    def _clear_delayed_effects(self, effect_dict: dict, effect_duration: int) -> None:
        """Remove delayed effects when they've expired.

        Parameters
        ----------
        effect_dict :
            Currently tracked effects.
        effect_duration :
            How long the effect lasts.
        """
        current_frame: int = self.ai.state.game_loop
        keys_to_remove: List[Point2] = []

        for position, frame_commenced in effect_dict.items():
            if current_frame - frame_commenced > effect_duration:
                keys_to_remove.append(position)

        for key in keys_to_remove:
            effect_dict.pop(key)

    def _add_delayed_effects_to_grids(
        self,
        cost: float,
        radius: float,
        effect_dict: Dict,
        react_on_frame: int,
    ) -> None:
        """Add the costs of the delayed effects to the grids.

        Parameters
        ----------
        cost :
            Cost of the effect.
        radius :
            How far around the center position the cost should be added.
        effect_dict :
            Currently tracked effects.
        react_on_frame :
            When units should begin reacting to this effect.
        """
        current_frame: int = self.ai.state.game_loop
        for position, frame_commenced in effect_dict.items():
            frame_difference: int = current_frame - frame_commenced
            if frame_difference >= react_on_frame:
                (
                    self.air_grid,
                    self.air_vs_ground_grid,
                    self.climber_grid,
                    self.ground_grid,
                    self.air_avoidance_grid,
                    self.ground_avoidance_grid,
                    self.priority_ground_avoidance_grid,
                ) = self.add_cost_to_multiple_grids(
                    position,
                    cost,
                    radius + self.config[PATHING][EFFECTS_RANGE_BUFFER],
                    [
                        self.air_grid,
                        self.air_vs_ground_grid,
                        self.climber_grid,
                        self.ground_grid,
                        self.air_avoidance_grid,
                        self.ground_avoidance_grid,
                        self.priority_ground_avoidance_grid,
                    ],
                )

    def _update_delayed_effects(self) -> None:
        """Update manually tracked effects."""
        # these effects disappear from the observation, so we have to manually add them
        self._add_delayed_effects_to_grids(
            cost=self.config[PATHING][EFFECTS][CORROSIVE_BILE][COST],
            radius=self.config[PATHING][EFFECTS][CORROSIVE_BILE][RANGE],
            effect_dict=self.biles_dict,
            react_on_frame=self.REACT_TO_BILES_ON_FRAME,
        )
        self._add_delayed_effects_to_grids(
            cost=self.config[PATHING][EFFECTS][NUKE][COST],
            radius=self.config[PATHING][EFFECTS][NUKE][RANGE],
            effect_dict=self.storms_dict,
            react_on_frame=self.REACT_TO_NUKES_ON_FRAME,
        )

        self._clear_delayed_effects(self.biles_dict, self.BILE_DURATION)
        self._clear_delayed_effects(self.storms_dict, self.NUKE_DURATION)
