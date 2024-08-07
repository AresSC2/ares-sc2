"""Calculations involving terrain.

"""
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set, Tuple

import numpy as np
from cython_extensions import cy_flood_fill_grid
from map_analyzer import MapData
from map_analyzer.constructs import ChokeArea, VisionBlockerArea
from sc2.game_info import Ramp
from sc2.ids.unit_typeid import UnitTypeId as UnitID
from sc2.position import Point2
from sc2.units import Units

from ares.cache import property_cache_once_per_frame
from ares.consts import (
    ALL_STRUCTURES,
    CURIOUS,
    DEBUG,
    DETECTORS,
    FLYING_IGNORE,
    GLITTERING,
    LIGHTSHADE,
    OXIDE,
    TOWNHALL_TYPES,
    ManagerName,
    ManagerRequestType,
    UnitTreeQueryType,
)
from ares.managers.manager import Manager
from ares.managers.manager_mediator import IManagerMediator, ManagerMediator

if TYPE_CHECKING:
    from ares import AresBot


class TerrainManager(Manager, IManagerMediator):
    """
    Anything to do with terrain:
        - expansion locations
        - natural / third base locations
        - overlord spots
        - behind mineral line spots
        - spore locations
    """

    CANT_BUILD_LOCATION_INVALID: int = 44
    cached_pathing_grid: np.ndarray
    choke_points: Set[Point2]
    current_siege_point: Point2
    current_siege_target: Point2
    map_data: MapData

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

        Returns
        -------

        """
        super().__init__(ai, config, mediator)
        self.manager_requests_dict = {
            ManagerRequestType.BUILDING_POSITION_BLOCKED_BY_BURROWED_UNIT: (
                lambda kwargs: self.building_position_blocked_by_burrowed_unit(**kwargs)
            ),
            ManagerRequestType.GET_BEHIND_MINERAL_POSITIONS: lambda kwargs: (
                self.get_behind_mineral_positions(**kwargs)
            ),
            ManagerRequestType.GET_CLOSEST_OVERLORD_SPOT: lambda kwargs: (
                self.get_closest_overlord_spot(**kwargs)
            ),
            ManagerRequestType.GET_DEFENSIVE_THIRD: lambda kwargs: self.defensive_third,
            ManagerRequestType.GET_ENEMY_EXPANSIONS: lambda kwargs: (
                self.enemy_expansions
            ),
            ManagerRequestType.GET_ENEMY_NAT: lambda kwargs: self.enemy_nat,
            ManagerRequestType.GET_ENEMY_RAMP: lambda kwargs: self.enemy_main_base_ramp,
            ManagerRequestType.GET_ENEMY_THIRD: lambda kwargs: self.enemy_third,
            ManagerRequestType.GET_ENEMY_FOURTH: lambda kwargs: self.enemy_fourth,
            ManagerRequestType.GET_FLOOD_FILL_AREA: lambda kwargs: (
                self.get_flood_fill_area(**kwargs)
            ),
            ManagerRequestType.GET_INITIAL_PATHING_GRID: lambda kwargs: (
                self.initial_pathing_grid
            ),
            ManagerRequestType.GET_IS_FREE_EXPANSION: lambda kwargs: (
                self.is_free_expansion
            ),
            ManagerRequestType.GET_MAP_CHOKE_POINTS: lambda kwargs: self.choke_points,
            ManagerRequestType.GET_OL_SPOTS: lambda kwargs: self.ol_spots,
            ManagerRequestType.GET_OWN_EXPANSIONS: lambda kwargs: self.own_expansions,
            ManagerRequestType.GET_OWN_NAT: lambda kwargs: self.own_nat,
            ManagerRequestType.GET_POSITIONS_BLOCKED_BY_BURROWED_ENEMY: lambda kwargs: (
                self.positions_blocked_by_enemy_burrowed_units
            ),
        }

        self.debug: bool = self.config[DEBUG]
        self.own_expansions: List[Tuple[Point2, float]] = []
        self.enemy_expansions: List[Tuple[Point2, float]] = []
        self.positions_blocked_by_enemy_burrowed_units: List[Point2] = []

        self.initial_pathing_grid: np.ndarray = (
            self.ai.game_info.pathing_grid.data_numpy.copy()
        )

        # needed a place to track spines until the spine positioning manager is done
        self.base_defense_spine_positions: Dict[Point2, int] = {}

    def initialise(self) -> None:
        """Calculate expansion locations from own and enemy perspective.

        Returns
        -------

        """
        if not self.ai.arcade_mode:
            self.own_expansions = self._calculate_expansion_path_distances(
                self.ai.start_location
            )

            self.enemy_expansions = self._calculate_expansion_path_distances(
                self.ai.enemy_start_locations[0]
            )

        self.map_data = self.manager_mediator.manager_request(
            ManagerName.PATH_MANAGER, ManagerRequestType.GET_MAP_DATA
        )
        self.choke_points: Set[Point2] = set(
            [point for ch in self.map_data.map_chokes for point in ch.points]
        )

        # used to make sure we don't accidentally query the fog of war
        self.cached_pathing_grid = self.manager_mediator.get_cached_ground_grid.copy()

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
        """Update positions blocked by burrowed enemies.

        Parameters
        ----------
        iteration :
            The game iteration.

        Returns
        -------

        """
        if self.debug and not self.ai.arcade_mode:
            await self._draw_information()

        self._clear_positions_blocked_by_burrowed_enemy()

    @property_cache_once_per_frame
    def defensive_third(self) -> Point2:
        """Get the third furthest from enemy.

        Returns
        -------
        Point2 :
            Location of the third base furthest from the enemy.

        """
        third_loc: Point2 = self.own_expansions[1][0]
        fourth_loc: Point2 = self.own_expansions[2][0]
        map_name: str = self.ai.game_info.map_name.upper()
        if OXIDE in map_name or GLITTERING in map_name:
            return fourth_loc

        third_distance_to_enemy: float = 0
        fourth_distance_to_enemy: float = 0
        for el in self.enemy_expansions:
            if el[0] == third_loc:
                third_distance_to_enemy = el[1]
            if el[0] == fourth_loc:
                fourth_distance_to_enemy = el[1]

        return (
            third_loc
            if third_distance_to_enemy >= fourth_distance_to_enemy
            else fourth_loc
        )

    @property_cache_once_per_frame
    def enemy_nat(self) -> Point2:
        """Calculate the enemy natural base.

        Returns
        -------
        Point2 :
            Location of the enemy natural base.

        """
        return self.enemy_expansions[0][0]

    @property_cache_once_per_frame
    def enemy_third(self) -> Point2:
        """Calculate the enemy third base.

        Notes
        -----
        Some manual adjustments are included for maps where distance to the main isn't
        the best metric of when a base should be taken.

        Returns
        -------
        Point2 :
            Location of the enemy third base.

        """
        map_name: str = self.ai.game_info.map_name.upper()
        # TODO: Some automatic analysis to decide which third we are interested in
        if (
            OXIDE in map_name
            or GLITTERING in map_name
            or LIGHTSHADE in map_name
            or CURIOUS in map_name
        ):
            return self.enemy_expansions[2][0]
        return self.enemy_expansions[1][0]

    @property_cache_once_per_frame
    def enemy_fourth(self) -> Point2:
        """Calculate the enemy fourth base.

        Returns
        -------
        Point2 :
            Location of the enemy fourth base.

        """
        if self.enemy_expansions[1][0] == self.enemy_third:
            return self.enemy_expansions[2][0]
        else:
            return self.enemy_expansions[1][0]

    @property_cache_once_per_frame
    def enemy_main_base_ramp(self) -> Ramp:
        """Identify which ramp is the enemies main.

        Returns
        -------
        Ramp :
            sc2 Ramp object for the opponent's main ramp.

        """
        return min(
            (ramp for ramp in self.ai.game_info.map_ramps if len(ramp.upper) in {2, 5}),
            key=lambda r: self.ai.enemy_start_locations[0].distance_to(r.top_center),
        )

    @property_cache_once_per_frame
    def is_free_expansion(self) -> bool:
        """Check all bases for a free expansion.

        Returns
        -------
        bool :
            True if there exists a free expansion, False otherwise.

        """
        for own_el in self.own_expansions:
            if not self.location_is_blocked(own_el[0]):
                return True
        return False

    @property_cache_once_per_frame
    def ol_spots(self) -> List[Point2]:
        """High ground Overlord hiding spots.

        Returns
        -------
        List[Point2] :
            List of Overlord hiding spots.

        """
        return [Point2(tuple_spot) for tuple_spot in self.map_data.overlord_spots]

    @property_cache_once_per_frame
    def ol_spot_near_enemy_natural(self) -> Point2:
        """Find an overlord spot near enemy natural for first overlord.

        Returns
        -------
        Point2 :
            Overlord spot near the enemy natural.

        """
        return self.get_closest_overlord_spot(self.enemy_nat)

    @property_cache_once_per_frame
    def own_nat(self) -> Point2:
        """Calculate our natural expansion.

        Returns
        -------
        Point2 :
            Location of our natural expansion.

        """
        return self.own_expansions[0][0]

    @property_cache_once_per_frame
    def own_third(self) -> Point2:
        """Calculate our third base.

        Returns
        -------
        Point2 :
            Location of our third base.

        """
        return self.own_expansions[1][0]

    @property_cache_once_per_frame
    def own_fourth(self) -> Point2:
        """Calculate our fourth base.

        Returns
        -------
        Point2 :
            Location of our fourth base.

        """
        return self.own_expansions[2][0]

    def get_closest_overlord_spot(self, from_pos: Point2) -> Point2:
        """Given a position, find the closest high ground overlord spot.

        Parameters
        ----------
        from_pos :
            Position the Overlord spot should be closest to.

        Returns
        -------
        Point2 :
            The closest Overlord hiding spot to the position.

        """
        min_distance: float = 999.9
        closest_spot: Point2 = self.ai.game_info.map_center
        for ol_spot in self.ol_spots:
            distance: float = ol_spot.distance_to(from_pos)
            if distance < min_distance:
                closest_spot = ol_spot
                min_distance = distance
        if closest_spot in self.ol_spots:
            # probably an unnecessary check, but just in case there's no overlord spot
            # by their natural
            self.ol_spots.pop(self.ol_spots.index(closest_spot))
        return closest_spot

    def get_flood_fill_area(self, start_point: Point2, max_dist: int = 25):
        """
        Given a point, flood fill outward from it and return the valid points.
        Does not continue through chokes.

        Parameters
        ----------
        start_point :
            Start flood fill outwards from this point.
        max_dist :
            Distance from start point before finishing the algorithm.

        Returns
        -------
        set :
            Set of points (as tuples) that are filled in
        """
        all_points = cy_flood_fill_grid(
            start_point=start_point.rounded,
            terrain_grid=self.ai.game_info.terrain_height.data_numpy.T,
            pathing_grid=self.cached_pathing_grid.astype(np.uint8),
            max_distance=max_dist,
            cutoff_points=self.choke_points,
        )
        return all_points

    def location_is_blocked(
        self, position: Point2, enemy_only: bool = False, structures_only: bool = False
    ) -> bool:
        """Checks if any structures or enemy units are near a location.

        At the moment, used to check an expansion is clear.

        Parameters
        ----------
        position :
            Position to check.
        enemy_only :
            Only check for enemy units.
        structures_only :
            Only check for structures.

        Returns
        -------
        bool :
            True if the position is considered blocked, False otherwise.

        """
        # TODO: Not currently an issue, but maybe we should consider rocks
        distance: float = 5.5
        close_enemy: Units = self.manager_mediator.get_units_in_range(
            start_points=[position],
            distances=distance,
            query_tree=UnitTreeQueryType.AllEnemy,
        )[0]

        close_enemy: Units = close_enemy.filter(
            lambda u: u.type_id not in FLYING_IGNORE
            and u.type_id != UnitID.AUTOTURRET
            and u.type_id != UnitID.MARINE
        )
        if structures_only and close_enemy(ALL_STRUCTURES):
            return True
        elif not structures_only and close_enemy:
            return True

        if not enemy_only:
            close_own: Units = self.manager_mediator.get_units_in_range(
                start_positions=[position],
                distances=3,
                query_tree=UnitTreeQueryType.AllOwn,
            )[0].filter(lambda u: u.type_id in TOWNHALL_TYPES)
            if close_own:
                return True

        return False

    def building_position_blocked_by_burrowed_unit(
        self, worker_tag: int, position: Point2
    ) -> Optional[Point2]:
        """See if the building position is blocked by a burrowed unit.

        Parameters
        ----------
        worker_tag :
            The worker attempting to build the structure.
        position :
            Where the structure is attempting to be placed.

        Returns
        -------
        Optional[Point2] :
            The position that's blocked by an enemy unit.

        """
        if not position:
            return
        # might not get action error if mine blows up the worker, save it immediately
        close_mines: Units = self.manager_mediator.get_units_in_range(
            start_points=[position],
            distance=3,
            query_tree=UnitTreeQueryType.EnemyGround,
        )[0].filter(lambda u: u.type_id == UnitID.WIDOWMINEBURROWED)
        if close_mines:
            self.positions_blocked_by_enemy_burrowed_units.append(position)
            return position

        for error in self.ai.state.action_errors:
            if (
                error.unit_tag == worker_tag
                and error.result == self.CANT_BUILD_LOCATION_INVALID
            ):
                self.positions_blocked_by_enemy_burrowed_units.append(position)
                return position

    def _calculate_expansion_path_distances(
        self, from_pos: Point2
    ) -> List[Tuple[Point2, float]]:
        """Calculates pathing distances to all expansions on the map
        from a given map position, returns list of expansions in order
        of pathing distance from from_pos

        TODO: This doesn't reach unpathable locations

        Parameters
        ----------
        from_pos : Point2

        Returns
        -------
        expansion_distances : List[Tuple[Point2, float]]
            List of Tuples where
                The first element is the location of the base.
                The second element is the pathing distance from `from_pos`.

        """
        expansion_distances: List[Tuple[Point2, float]] = []
        grid: np.ndarray = self.manager_mediator.get_ground_grid
        for el in self.ai.expansion_locations_list:
            if from_pos.distance_to(el) < self.ai.EXPANSION_GAP_THRESHOLD:
                continue

            if path := self.manager_mediator.get_map_data_object.pathfind(
                from_pos, el, grid
            ):
                expansion_distances.append((el, len(path)))

        # sort by path length to each expansion
        expansion_distances = sorted(expansion_distances, key=lambda x: x[1])
        return expansion_distances

    def get_behind_mineral_positions(self, th_pos: Point2) -> List[Point2]:
        """Finds 3 spots behind the mineral line

        Notes
        -----
        This is useful for building structures out of typical cannon range.

        Parameters
        ----------
        th_pos :
            Position of townhall to find points behind the mineral line of.

        Returns
        -------
        List[Point2] :
            Points behind the mineral line of the designated base.

        """
        positions: List[Point2] = []
        possible_behind_mineral_positions: List[Point2] = []

        all_mf: Units = self.ai.mineral_field.closer_than(10, th_pos)

        if all_mf:
            for mf in all_mf:
                possible_behind_mineral_positions.append(th_pos.towards(mf.position, 9))

            positions.append(th_pos.towards(all_mf.center, 9))  # Center
            positions.insert(
                0, positions[0].furthest(possible_behind_mineral_positions)
            )
            positions.append(positions[0].furthest(possible_behind_mineral_positions))
        # no minerals at base, give up trying to work it out
        else:
            positions.append(th_pos.towards(self.ai.game_info.map_center, 5))
            positions.append(th_pos.towards(self.ai.game_info.map_center, 5))
            positions.append(th_pos.towards(self.ai.game_info.map_center, 5))

        return positions

    def get_base_to_choke_information(self) -> Dict[Point2, Dict[ChokeArea, int]]:
        """Get pathing distance from each base to every choke point on the map.

        VisionBlockerArea chokes are currently ignored.

        Returns
        -------
        Dict[Point2, Dict[ChokeArea, int]] :
            Key is the base location
            Value is a dictionary where the key is the choke point and the value is the
                length of the path to that choke point.

        """
        final_dict = {
            base_loc: {
                ch: len(
                    self.map_data.pathfind(
                        base_loc,
                        ch.center,
                        self.manager_mediator.get_cached_ground_grid,
                    )
                )
                for ch in self.map_data.in_region_p(base_loc).region_chokes
                if type(ch) is not VisionBlockerArea
            }
            for base_loc in self.ai.expansion_locations_list
        }
        return final_dict

    def _clear_positions_blocked_by_burrowed_enemy(self) -> None:
        """Determine if locations blocked by enemies are still blocked.

        Recalculates the blocked positions list.

        Returns
        -------

        """
        _positions_blocked_by_enemy_burrowed_units: List[Point2] = []
        for position in self.positions_blocked_by_enemy_burrowed_units:
            detectors: Units = self.manager_mediator.get_units_in_range(
                start_points=[position], distance=7, query_tree=UnitTreeQueryType.AllOwn
            )[0].filter(lambda u: u.type_id in {DETECTORS})
            enemies_in_range: Units = self.manager_mediator.get_units_in_range(
                start_points=[position],
                distance=9,
                query_tree=UnitTreeQueryType.AllEnemy,
            )[0]

            # looks like there is nothing here, no need to add it to the blocked
            # positions list
            if detectors and not enemies_in_range:
                continue

            _positions_blocked_by_enemy_burrowed_units.append(position)

        self.positions_blocked_by_enemy_burrowed_units = (
            _positions_blocked_by_enemy_burrowed_units
        )

    async def _draw_information(self) -> None:  # pragma: no cover
        self.ai.draw_text_on_world(self.own_nat, "Natural")
        self.ai.draw_text_on_world(self.own_third, f"Third {self.own_third}")
        self.ai.draw_text_on_world(self.own_fourth, f"Fourth {self.own_fourth}")
        self.ai.draw_text_on_world(self.enemy_nat, "Enemy Natural")
        self.ai.draw_text_on_world(self.enemy_third, "Enemy Third")
        self.ai.draw_text_on_world(self.enemy_fourth, "Enemy Fourth")

        self.ai.draw_text_on_world(self.enemy_main_base_ramp.top_center, "Enemy Ramp")

        for i, el in enumerate(self.own_expansions):
            self.ai.draw_text_on_world(el[0], str(i), y_offset=2)
