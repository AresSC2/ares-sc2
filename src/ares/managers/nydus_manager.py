from collections import defaultdict, deque
from typing import TYPE_CHECKING, Any, DefaultDict, Union

import numpy as np
from cython_extensions.geometry import cy_distance_to_squared, cy_towards
from cython_extensions.units_utils import cy_closest_to
from map_analyzer import Region
from sc2.data import Race
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId as UnitID
from sc2.position import Point2
from sc2.unit import Unit
from scipy.spatial import KDTree

from ares.consts import (
    ENTRY,
    EXIT,
    EXIT_TOWARDS,
    UNIT_TYPE,
    ManagerName,
    ManagerRequestType,
)
from ares.managers.manager import Manager
from ares.managers.manager_mediator import IManagerMediator, ManagerMediator

if TYPE_CHECKING:
    from ares import AresBot


class NydusManager(Manager, IManagerMediator):
    enemy_main_region: Region
    UNIT_NYDUS_TRAVEL_BAN_DURATION: float = 5.0

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
        super().__init__(ai, config, mediator)

        self.all_enemy_main_nydus_points: list[Point2] = [
            self.ai.enemy_start_locations[0]
        ]
        self.all_own_main_nydus_points: list[Point2] = [self.ai.start_location]

        # key is tag of travelling unit,
        # value is dictionary of tags of ENTRY/EXIT nodes and UnitID
        self._nydus_travellers: dict[
            int, dict[str, Union[int, Point2, UnitID]]
        ] = dict()
        self._nydus_tags_with_actions: set[int] = set()
        # if unit just left nydus, it will be banned from nydus travel for a bit
        self._units_banned_from_travelling: dict[int, float] = {}

        self.manager_requests_dict = {
            ManagerRequestType.FIND_NYDUS_AT_LOCATION: (
                lambda kwargs: self._find_nydus_at_location(**kwargs)
            ),
            ManagerRequestType.GET_BANNED_NYDUS_TRAVELLERS: (
                lambda kwargs: self._units_banned_from_travelling
            ),
            ManagerRequestType.GET_ENEMY_MAIN_NYDUS_POINTS: (
                lambda kwargs: self.all_enemy_main_nydus_points
            ),
            ManagerRequestType.GET_PRIMARY_NYDUS_ENEMY_MAIN: (
                lambda kwargs: self.primary_nydus_enemy_main
            ),
            ManagerRequestType.GET_PRIMARY_NYDUS_OWN_MAIN: (
                lambda kwargs: self.primary_nydus_own_main
            ),
            ManagerRequestType.ADD_TO_NYDUS_TRAVELLERS: (
                lambda kwargs: self._add_to_nydus_travellers(**kwargs)
            ),
            ManagerRequestType.CLEAR_NYDUS_TRAVELLERS: (
                lambda kwargs: self._nydus_travellers.clear()
            ),
            ManagerRequestType.GET_NYDUS_TRAVELLERS: (
                lambda kwargs: self._nydus_travellers
            ),
            ManagerRequestType.REMOVE_FROM_NYDUS_TRAVELLERS: (
                lambda kwargs: self._remove_from_nydus_travellers(**kwargs)
            ),
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
            The result of the request
        """
        return self.manager_requests_dict[request](kwargs)

    @property
    def primary_nydus_enemy_main(self) -> Point2:
        """
        Find Nydus location in their main.
        """
        if not self.all_enemy_main_nydus_points:
            return Point2(
                cy_towards(
                    self.ai.enemy_start_locations[0], self.ai.game_info.map_center, 10
                )
            )
        else:
            return self.all_enemy_main_nydus_points[0]

    @property
    def primary_nydus_own_main(self) -> Point2:
        """
        Find Nydus location in their main.
        """
        if not self.all_own_main_nydus_points:
            return Point2(
                cy_towards(self.ai.start_location, self.ai.game_info.map_center, 10)
            )
        else:
            return self.all_own_main_nydus_points[0]

    def initialise(self) -> None:
        """Supply the manager with information
        that requires the game to have launched."""
        if self.ai.arcade_mode:
            return

        if enemy_main_region := self.manager_mediator.get_map_data_object.in_region_p(
            self.ai.enemy_start_locations[0]
        ):
            self.all_enemy_main_nydus_points = self._calculate_nydus_main_positions(
                enemy_main_region,
                self.ai.enemy_start_locations[0],
                self.manager_mediator.get_enemy_ramp.top_center,
            )

        if own_main_region := self.manager_mediator.get_map_data_object.in_region_p(
            self.ai.start_location
        ):
            self.all_own_main_nydus_points = self._calculate_nydus_main_positions(
                own_main_region,
                self.ai.start_location,
                self.ai.main_base_ramp.top_center,
            )

    async def update(self, iteration: int) -> None:
        if self.ai.arcade_mode:
            return
        if self.ai.race == Race.Zerg:
            self._nydus_tags_with_actions.clear()
            # handle units
            await self._handle_nydus_travellers()
            self._review_travel_bans()

        if self.config["Debug"]:
            self._draw_information()

    def _calculate_nydus_main_positions(
        self, region: Region, main_location: Point2, ramp_location: Point2
    ) -> list[Point2]:
        """
        Calculate Nydus locations in the main base that meet the following criteria:
            - the location is pathable
            - the location is 9 away from gas geysers
            - the location is 13 away from the ramp
            - the location is at the edge of the base
        """
        gas_distance: float = 11.0
        pathable_perimeter = [
            point
            for point in region.perimeter_points
            if self.ai.game_info.pathing_grid[point]
        ]
        # generate KDTree for nearest neighbor searching of perimeter points
        tree = KDTree(pathable_perimeter)

        # find spaces too close to the enemy townhall
        close_to_townhall = {
            pathable_perimeter[i] for i in tree.query_ball_point(main_location, 15)
        }

        # find spaces too close to the gases in enemy main
        enemy_gases = self.ai.vespene_geyser.filter(
            lambda g: cy_distance_to_squared(g.position, main_location) < 144.0
        )
        gas_one = [
            pathable_perimeter[x]
            for x in tree.query_ball_point(enemy_gases[0].position, gas_distance)
        ]
        gas_two = [
            pathable_perimeter[y]
            for y in tree.query_ball_point(enemy_gases[1].position, gas_distance)
        ]
        close_to_gas = set(gas_one + gas_two)

        # find spaces too close to the ramp in enemy main
        close_to_ramp = {
            pathable_perimeter[z] for z in tree.query_ball_point(ramp_location, 13)
        }

        # separated into steps for debugging

        # remove points too close to ramp
        perimeter_away_from_ramp = set(pathable_perimeter) - close_to_ramp

        perimeter_away_from_gas_and_ramp = perimeter_away_from_ramp - close_to_gas

        perimeter_away_from_gas_and_ramp_and_townhall = (
            perimeter_away_from_gas_and_ramp - close_to_townhall
        )

        potential_points = [
            Point2(spot) for spot in perimeter_away_from_gas_and_ramp_and_townhall
        ]

        # maximize the sum of the distances from the townhall and ramp
        nydus_spots = sorted(
            potential_points,
            key=lambda point: -(
                cy_distance_to_squared(point, main_location)
                + cy_distance_to_squared(point, ramp_location)
            ),
        )

        return nydus_spots

    def _find_nydus_at_location(
        self,
        base_location: Point2,
        min_base_distance: float = 15.0,
        max_nydus_distance: float = 25.0,
        max_cost: int = 20,
    ) -> Union[None, Point2]:
        """
        Find a Nydus position with pathing cost less than max_cost in
        a region containing the given point, at least
        min_distance from an enemy base and no more than max_distance
        from the target point.
        """
        if base_location == self.ai.enemy_start_locations[0]:
            return self.primary_nydus_enemy_main
        elif base_location == self.ai.start_location:
            return self.primary_nydus_own_main

        region: Region = self.manager_mediator.get_map_data_object.in_region_p(
            base_location
        )
        if not region:
            return None

        grid: np.ndarray = self.manager_mediator.get_ground_grid
        min_base_distance_sq: float = min_base_distance**2
        max_nydus_distance_sq: float = max_nydus_distance**2
        region_costs = {
            point: grid[point]
            for point in region.points
            if cy_distance_to_squared(point, base_location) <= max_nydus_distance_sq
            and min([cy_distance_to_squared(point, b) for b in region.bases])
            >= min_base_distance_sq
        }

        if not region_costs:
            return None

        min_cost = min(region_costs.values())
        if min_cost >= max_cost:
            # all tiles are too expensive
            return None

        potential_locations: list[Point2] = [
            Point2(point) for point in region_costs if region_costs[point] == min_cost
        ]

        # no potential locations found
        if len(potential_locations) == 0:
            return None

        # see if any enemies are in range 12 of each point
        enemy_in_range_of_points: list[
            bool
        ] = self.manager_mediator.get_any_enemies_in_range(
            positions=potential_locations, radius=12.0
        )
        # points that are far enough away
        distanced_locations: list[Point2] = [
            potential_locations[i]
            for i in range(len(potential_locations))
            if not enemy_in_range_of_points[i]
        ]
        if not distanced_locations:
            # no suitable place to build a Nydus
            return None
        else:
            # choose the closest location to the base_location, preferring visible spots
            visible_locations: list[Point2] = [
                loc for loc in distanced_locations if self.ai.state.visibility[loc] == 2
            ]
            candidates: list[Point2] = (
                visible_locations if visible_locations else distanced_locations
            )
            final: Point2 = min(
                candidates, key=lambda p: cy_distance_to_squared(p, base_location)
            )
            return final

    def _add_to_nydus_travellers(
        self,
        unit: Unit,
        entry_nydus_tag: int,
        exit_nydus_tag: int,
        exit_towards: Point2,
    ) -> None:
        self._nydus_travellers[unit.tag] = {
            ENTRY: entry_nydus_tag,
            EXIT: exit_nydus_tag,
            EXIT_TOWARDS: exit_towards,
            UNIT_TYPE: unit.type_id,
        }

    def _remove_from_nydus_travellers(self, unit_tag: int) -> None:
        if unit_tag in self._nydus_travellers:
            del self._nydus_travellers[unit_tag]

    def _draw_information(self):
        self.ai.draw_text_on_world(self.primary_nydus_enemy_main, "Enemy Main Nydus")
        self.ai.draw_text_on_world(self.primary_nydus_own_main, "Own Main Nydus")

        # for location in self.ai.expansion_locations_list:
        #     if position := self._find_nydus_at_location(base_location=location):
        #         self.ai.draw_text_on_world(position, "Nydus Canal Placement")

    async def _handle_nydus_travellers(self):
        own_structures_dict: dict = self.manager_mediator.get_own_structures_dict
        nyduses: list[Unit] = (
            own_structures_dict[UnitID.NYDUSNETWORK]
            + own_structures_dict[UnitID.NYDUSCANAL]
        )
        num_nyduses: int = len(nyduses)
        # no nydus? clear all data about passengers, no need to do anything else
        if num_nyduses == 0:
            self._nydus_travellers.clear()
            return

        # only one nydus? get everyone out
        elif num_nyduses == 1:
            # it looks like there are no travelers? no need to do anything else
            if len(self._nydus_travellers) == 0:
                return

            for traveller_tag in self._nydus_travellers:
                self._nydus_travellers[traveller_tag][EXIT] = nyduses[0].tag

        # arrange the order units get out
        passengers: set[int] = nyduses[0].passengers_tags
        exit_queue: DefaultDict[int, deque[int]] = defaultdict(deque)
        for traveller_tag in passengers:
            if traveller_tag in self._nydus_travellers:
                if self._nydus_travellers[traveller_tag][UNIT_TYPE] == UnitID.QUEEN:
                    exit_queue[self._nydus_travellers[traveller_tag][EXIT]].appendleft(
                        traveller_tag
                    )
                else:
                    exit_queue[self._nydus_travellers[traveller_tag][EXIT]].append(
                        traveller_tag
                    )
        nydus_tag_to_object = {nydus.tag: nydus for nydus in nyduses}
        for tag in exit_queue:
            nydus: Unit | None = nydus_tag_to_object.get(tag, None)
            if (
                nydus
                and nydus.is_ready
                and exit_queue[tag]
                and nydus.tag not in self._nydus_tags_with_actions
            ):
                unit_tag = exit_queue[tag][0]
                nydus(
                    AbilityId.RALLY_BUILDING,
                    self._nydus_travellers[unit_tag][EXIT_TOWARDS],
                )
                await self.ai.unload_by_tag(nydus, unit_tag)
                self._nydus_tags_with_actions.add(nydus.tag)
                self._units_banned_from_travelling[unit_tag] = self.ai.time

        exit_nydus: Unit = cy_closest_to(self.manager_mediator.get_own_nat, nyduses)
        for trapped_traveller in passengers - set(self._nydus_travellers.keys()):
            # units that are stuck in the Nydus,
            # should only happen if it dies during an unload
            self._nydus_travellers[trapped_traveller] = {
                ENTRY: exit_nydus.tag,
                EXIT: exit_nydus.tag,
                EXIT_TOWARDS: self.ai.game_info.map_center,
                UNIT_TYPE: None,
            }

    def remove_destroyed_nydus(self, unit_tag: int) -> None:
        """Sanitize traveller mappings when a Nydus (network/canal) is destroyed.

        The destroyed tag could be referenced as either ENTRY or EXIT for any traveller.
        Reassign those references to a surviving Nydus if one exists; otherwise,
        clear all travellers.
        """
        # Gather surviving nyduses
        own_structures_dict: dict = self.manager_mediator.get_own_structures_dict
        nyduses: list[Unit] = (
            own_structures_dict[UnitID.NYDUSNETWORK]
            + own_structures_dict[UnitID.NYDUSCANAL]
        )

        # If none remain, clear travellers and return
        if not nyduses:
            self._nydus_travellers.clear()
            return

        # Choose a reasonable fallback nydus (closest to our natural)
        fallback_nydus: Unit = cy_closest_to(self.manager_mediator.get_own_nat, nyduses)
        fallback_tag: int = fallback_nydus.tag

        # Update any traveller entries that referenced the destroyed tag
        for traveller_tag in list(self._nydus_travellers.keys()):
            data = self._nydus_travellers[traveller_tag]

            if data.get(ENTRY) == unit_tag:
                data[ENTRY] = fallback_tag

            if data.get(EXIT) == unit_tag:
                data[EXIT] = fallback_tag

    def _review_travel_bans(self):
        keys_to_remove: list[int] = []
        for unit_tag in self._units_banned_from_travelling:
            if (
                self.ai.time
                > self._units_banned_from_travelling[unit_tag]
                + self.UNIT_NYDUS_TRAVEL_BAN_DURATION
            ):
                keys_to_remove.append(unit_tag)
        for key in keys_to_remove:
            del self._units_banned_from_travelling[key]
