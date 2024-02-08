from collections import defaultdict
from enum import Enum, auto
from typing import DefaultDict, Union

from cython_extensions import cy_closest_to
from sc2.unit import Unit
from sc2.units import Units

from ares.consts import (
    DEBUG,
    DISTANCES,
    FLYING_ENEMY_LEAVING_BASES,
    FLYING_ENEMY_NEAR_BASES,
    GROUND_ENEMY_LEAVING_BASES,
    GROUND_ENEMY_NEAR_BASES,
    ManagerName,
    ManagerRequestType,
    UnitTreeQueryType,
)
from ares.managers.manager import Manager
from ares.managers.manager_mediator import IManagerMediator, ManagerMediator


class EnemyType(Enum):
    FLYING = auto()
    GROUND = auto()


class EnemyToBaseManager(Manager, IManagerMediator):
    """Keep track of enemies at our bases.

    Attributes
    ----------
    ground_enemy_near_bases : dict[int : set[int]
        Dictionary where keys are townhall tags
        And values are tags of enemy ground near that base
    flying_enemy_near_bases : dict[int : set[int]
        Same as above but for flying enemy
    main_enemy_air_threats_near_townhall : Units
        The largest enemy air force near our bases.
    main_enemy_ground_threats_near_townhall :
        The largest enemy ground force near our bases.
    """

    def __init__(self, ai, config: dict, mediator: ManagerMediator) -> None:
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
        super(EnemyToBaseManager, self).__init__(ai, config, mediator)
        self.manager_requests_dict = {
            ManagerRequestType.GET_FLYING_ENEMY_NEAR_BASES: (
                lambda kwargs: self.flying_enemy_near_bases
            ),
            ManagerRequestType.GET_GROUND_ENEMY_NEAR_BASES: (
                lambda kwargs: self.ground_enemy_near_bases
            ),
            ManagerRequestType.GET_MAIN_AIR_THREATS_NEAR_TOWNHALL: (
                lambda kwargs: self.main_enemy_air_threats_near_townhall
            ),
            ManagerRequestType.GET_MAIN_GROUND_THREATS_NEAR_TOWNHALL: (
                lambda kwargs: self.main_enemy_ground_threats_near_townhall
            ),
            ManagerRequestType.GET_TH_TAG_WITH_LARGEST_GROUND_THREAT: (
                lambda kwargs: self.th_tag_largest_ground_threat
            ),
        }

        # key:townhall tag, value: Enemy ground units near that base
        self.ground_enemy_near_bases: DefaultDict[
            int,
            set[int],
        ] = defaultdict(set)
        # key:townhall tag, value: Enemy flying units near that base
        self.flying_enemy_near_bases: DefaultDict[
            int,
            set[int],
        ] = defaultdict(set)

        self.ground_enemy_leaving_bases_dist: float = float(
            self.config[DISTANCES][GROUND_ENEMY_LEAVING_BASES]
        )
        self.flying_enemy_leaving_bases_dist: float = float(
            self.config[DISTANCES][FLYING_ENEMY_LEAVING_BASES]
        )

        self.ground_enemy_near_bases_dist: float = float(
            self.config[DISTANCES][GROUND_ENEMY_NEAR_BASES]
        )
        self.flying_enemy_near_bases_dist: float = float(
            self.config[DISTANCES][FLYING_ENEMY_NEAR_BASES]
        )

        self.main_enemy_air_threats_near_townhall: Units = Units([], ai)
        self.main_enemy_ground_threats_near_townhall: Units = Units([], ai)
        self.th_tag_largest_ground_threat: int = 0

    def manager_request(
        self,
        receiver: ManagerName,
        request: ManagerRequestType,
        reason: str = None,
        **kwargs,
    ) -> Union[dict, int, Units]:
        """Fetch information from this Manager so another Manager can use it.

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
        Union[dict, int, Units] :
            Types that can be returned from mediator requests via this manager.

        """
        return self.manager_requests_dict[request](kwargs)

    async def update(self, _iteration: int) -> None:
        """Keep track of enemy at our bases.

        Parameters
        ----------
        _iteration :
            The current game iteration
        """
        # look for enemies near our bases
        self._look_for_enemy_near_bases()

        # look for enemies leaving our bases:
        th_tags: list[int] = self._check_if_enemy_left_bases(
            self.ground_enemy_near_bases,
            self.ground_enemy_leaving_bases_dist,
            EnemyType.GROUND,
        )
        self._clear_data_structures(th_tags, EnemyType.GROUND)
        # flying enemies leaving:
        th_tags: list[int] = self._check_if_enemy_left_bases(
            self.flying_enemy_near_bases,
            self.flying_enemy_leaving_bases_dist,
            EnemyType.FLYING,
        )
        self._clear_data_structures(th_tags, EnemyType.FLYING)

        self.main_enemy_air_threats_near_townhall = self._get_largest_enemy_threat(
            self.flying_enemy_near_bases, EnemyType.FLYING
        )
        self.main_enemy_ground_threats_near_townhall = self._get_largest_enemy_threat(
            self.ground_enemy_near_bases, EnemyType.GROUND
        )

        if self.config[DEBUG]:
            self._print_debug_info()

    def _look_for_enemy_near_bases(self) -> None:
        """
        Look for new enemy units near our bases.
        """
        if not self.ai.townhalls:
            return

        th_to_nearby_ground_units_dict = self.manager_mediator.get_units_in_range(
            start_points=self.ai.townhalls,
            distances=self.ground_enemy_near_bases_dist,
            query_tree=UnitTreeQueryType.EnemyGround,
            return_as_dict=True,
        )

        th_to_nearby_flying_units_dict = self.manager_mediator.get_units_in_range(
            start_points=self.ai.townhalls,
            distances=self.flying_enemy_near_bases_dist,
            query_tree=UnitTreeQueryType.EnemyFlying,
            return_as_dict=True,
        )

        for th in self.ai.townhalls:
            th_tag: int = th.tag
            if ground_enemy_units := th_to_nearby_ground_units_dict[th_tag]:
                self._update_units_near_townhall(
                    ground_enemy_units, th_tag, self.ground_enemy_near_bases
                )

            if flying_enemy_units := th_to_nearby_flying_units_dict[th_tag]:
                self._update_units_near_townhall(
                    flying_enemy_units, th_tag, self.flying_enemy_near_bases
                )

    def _update_units_near_townhall(
        self, enemy_units: Units, th_tag: int, th_to_unit_dict: dict[int, set[int]]
    ) -> None:
        """Check `enemy_units` and add newly found units to `th_to_unit_dict`.

        Parameters
        ----------
        enemy_units :
            Close enemy units found at this base with `th_tag`.
        th_tag :
            Tag of the townhall unit these enemies are near.
        th_to_unit_dict :
            The dictionary we want to update.
        """
        for unit in enemy_units:
            if not unit.is_visible:
                continue
            unit_tag: int = unit.tag
            if unit_tag not in th_to_unit_dict[th_tag]:
                th_to_unit_dict[th_tag].add(unit_tag)

    def _check_if_enemy_left_bases(
        self,
        th_to_enemy_units_dict: dict[int, set[int]],
        distance: float,
        enemy_type: EnemyType,
    ) -> list[int]:
        """
        Checks the closest enemy to base, if far enough away delete the item
        from the dict.

        Parameters
        ----------
        th_to_enemy_units_dict :
            The dictionary we should try to remove enemy unit tags from.
        distance :
            The distance at which we declare enemy is far away from.
        enemy_type :
            Ground or Fliers.

        Returns
        ----------
        list[int] :
            Returns a list of the townhall tags where enemy has left.
        """
        # keys that will be deleted from the enemy dict
        keys_to_delete: list[int] = []
        for th_tag, enemy_tags in th_to_enemy_units_dict.items():
            th: Unit = self.ai.unit_tag_dict.get(th_tag, None)
            if not th or len(enemy_tags) == 0:
                # no townhall or enemy? safe to remove from bookkeeping
                keys_to_delete.append(th_tag)
                continue

            query_type: UnitTreeQueryType = (
                UnitTreeQueryType.EnemyGround
                if enemy_type == EnemyType.GROUND
                else UnitTreeQueryType.EnemyFlying
            )

            close_enemy: Units = self.manager_mediator.get_units_in_range(
                start_points=[th],
                distances=distance,
                query_tree=query_type,
            )[0]

            # check if enemy army far enough from this base
            if close_enemy:
                closest_enemy: Unit = cy_closest_to(th.position, close_enemy)
                # if closest enemy has gone into fog of war
                if closest_enemy.distance_to(th) > distance or closest_enemy.is_memory:
                    keys_to_delete.append(th_tag)
            else:
                # there is nothing here, remove th
                keys_to_delete.append(th_tag)

        return keys_to_delete

    def _clear_data_structures(self, th_tags: list[int], enemy_type: EnemyType) -> None:
        """Given `th_tags`, remove records from the relevant bookkeeping.

        Parameters
        ----------
        th_tags :
            The tags we should look for in the dictionaries.
        enemy_type :
            Ground or Fliers.
        """
        for th_tag in th_tags:
            if enemy_type == EnemyType.FLYING:
                del self.flying_enemy_near_bases[th_tag]
            elif enemy_type == EnemyType.GROUND:
                del self.ground_enemy_near_bases[th_tag]

    def _get_largest_enemy_threat(
        self, th_enemies_dict: dict[int, set[int]], enemy_type: EnemyType
    ) -> Units:
        """Given `th_tags`, remove records from the relevant bookkeeping.

        Parameters
        ----------
        th_enemies_dict :
            The dictionary in which we are searching for the largest threat.
        enemy_type :
            Ground or Fliers.

        Returns
        ----------
        Units :
            The enemy Units collection of the largest threat.
        """
        largest_enemy_supply: float = 0.0
        enemy_force: Units = Units([], self.ai)
        for th_tag, enemy_tags in th_enemies_dict.items():
            enemy: Units = self.ai.enemy_units.tags_in(enemy_tags)
            if enemy.amount == 0:
                continue
            supply_enemy: float = self.ai.get_total_supply(enemy)
            if supply_enemy > largest_enemy_supply:
                largest_enemy_supply = supply_enemy
                enemy_force = enemy
                # store the tag of the th with the largest ground threat
                if enemy_type == EnemyType.GROUND:
                    self.th_tag_largest_ground_threat = th_tag
        return enemy_force

    def _print_debug_info(self) -> None:
        """
        Draw on screen tags of recorded townhall and enemy tags near
        our bases.
        """

        def print_info_from_dict(ground_to_enemy_dict: dict) -> None:
            for th_tag, enemy_tags in ground_to_enemy_dict.items():
                if th := self.ai.unit_tag_dict.get(th_tag, None):
                    self.ai.draw_text_on_world(th.position, f"TH - {th.tag}")
                    enemies: list[Unit] = [
                        e for e in self.ai.all_enemy_units if e.tag in enemy_tags
                    ]
                    for enemy in enemies:
                        self.ai.draw_text_on_world(
                            enemy.position, f"{enemy.tag} found near {th.tag}"
                        )

        # print on screen info about what enemy has been found near each base
        print_info_from_dict(self.ground_enemy_near_bases)
        print_info_from_dict(self.flying_enemy_near_bases)
