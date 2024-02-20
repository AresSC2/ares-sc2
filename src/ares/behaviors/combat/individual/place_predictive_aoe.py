import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Optional, Tuple

from sc2.ids.ability_id import AbilityId
from sc2.position import Point2
from sc2.unit import Unit

from ares.behaviors.combat.individual.combat_individual_behavior import (
    CombatIndividualBehavior,
)
from ares.managers.manager_mediator import ManagerMediator

if TYPE_CHECKING:
    from ares import AresBot


@dataclass
class PlacePredictiveAoE(CombatIndividualBehavior):
    """Predict an enemy position and fire AoE accordingly.

    Warning: Use this at your own risk. Work in progress.

    TODO: Guess where the enemy is going based on how it's been moving.
        Cythonize this.

    Attributes
    ----------
    unit: Unit
        The unit to fire the AoE.
    path : List[Point2]
        How we're getting to the target position (the last point in the list)
    enemy_center_unit: Unit
        Enemy unit to calculate positions based on.
    aoe_ability: AbilityId
        AoE ability to use.
    ability_delay: int
        Amount of frames between using the ability and the ability occurring.
    """

    unit: Unit
    path: List[Point2]
    enemy_center_unit: Unit
    aoe_ability: AbilityId
    ability_delay: int

    def execute(
        self, ai: "AresBot", config: dict, mediator: ManagerMediator, **kwargs
    ) -> bool:
        if self.aoe_ability in self.unit.abilities:
            # try to fire the ability if we find a position
            if pos := self._calculate_target_position(ai):
                if ai.is_visible(pos):
                    return self.unit(self.aoe_ability, pos)
        # no position found or the ability isn't ready
        return False

    def _calculate_target_position(self, ai: "AresBot") -> Point2:
        """Calculate where we want to put the AoE.

        Returns
        -------
        Point2 :
            Where we want to place the AoE.

        """
        # figure out where our unit is going to be during the chase
        own_unit_path = self._get_unit_real_path(self.path, self.unit.distance_per_step)

        # enemy path, assuming it moves directly towards our unit at all times
        chasing_path, _reached_target = self._get_chasing_unit_path(
            own_unit_path,
            self.enemy_center_unit.position,
            self.enemy_center_unit.distance_per_step,
        )

        # pick the spot along the predicted path that the enemy will have reached when
        # the ability goes off
        delayed_idx = math.ceil(self.ability_delay / ai.client.game_step)

        return chasing_path[min(delayed_idx, len(chasing_path) - 1)]

    @staticmethod
    def _get_unit_next_position(
        current_position: Point2,
        current_target: Point2,
        distance_per_step: float,
        next_target: Optional[Point2] = None,
    ) -> Tuple[Point2, bool]:
        """Calculate where a unit will be on the next step.

        Assumes knowledge of the unit's current position, target position, and that the
        unit will not change direction.

        TODO: handle the case where the unit is fast enough to travel multiple path
            points per game step

        Parameters
        ----------
        current_position: Point2
            Where the unit currently is.
        current_target: Point2
            Where the unit is going.
        distance_per_step: float
            How far the unit moves per game step.
        next_target: Optional[Point2]
            Where the unit should head if it reaches the target point between steps.

        Returns
        -------
        Tuple[Point2, bool] :
            Point2 is where the unit will be
            bool is whether the unit reached `current_target` in this step

        """
        reached_target: bool = False

        # make sure we won't run past the target point
        distance_to_target: float = current_position.distance_to(current_target)
        if distance_to_target < distance_per_step:
            if next_target:
                """
                Overwrite initial values to reflect moving from the current target
                to the next position.
                """
                distance_per_step = (
                    1 - distance_to_target / distance_per_step
                ) * distance_per_step
                current_position = current_target
                current_target = next_target
                reached_target = True
            else:
                # we don't have a next point to go to, so stop at the current target
                return current_target, True

        # offset the current position towards the target position by the amount of
        # distance covered per game step
        return (
            current_position.towards(current_target, distance_per_step),
            reached_target,
        )

    def _get_unit_real_path(
        self, unit_path: List[Point2], unit_speed: float
    ) -> List[Point2]:
        """Find the location of the unit at each game step given its path.

        Parameters
        ----------
        unit_path: List[Point2]
            Where the unit is being told to move.
        unit_speed: float
            How far the unit moves each game step.

        Returns
        -------
        List[Point2] :
            Where the unit will be at each game iteration.

        """
        real_path: List[Point2] = [unit_path[0]]
        curr_target_idx: int = 1
        # 100 should be overkill, but I'm really just trying to avoid a `while` loop
        for step in range(100):
            if curr_target_idx >= len(unit_path):
                # we've made it to the end of the path
                break
            # travel directly towards the next point on the path, updating the target
            # point when the one before it is reached
            next_position, increase_target_idx = self._get_unit_next_position(
                current_position=real_path[-1],
                current_target=unit_path[curr_target_idx],
                distance_per_step=unit_speed,
                next_target=unit_path[curr_target_idx + 1]
                if curr_target_idx != len(unit_path) - 1
                else None,
            )
            real_path.append(next_position)

            if increase_target_idx:
                # we made it to the current target point, get the next one
                curr_target_idx += 1

        return real_path

    def _get_chasing_unit_path(
        self, target_unit_path: List[Point2], start_position: Point2, unit_speed: float
    ) -> Tuple[List[Point2], bool]:
        """Calculate the path the chasing unit will take to catch the target unit.

        Arguments
        ---------
        target_unit_path: List[Point2]
            Where the target unit is going to be at each game iteration.
        start_position: Point2
            Where the chasing unit is starting from.
        unit_speed: float
            How far the chasing unit moves per game step.

        Returns
        -------
        Tuple[List[Point2], bool] :
            List[Point2] is the chasing unit's path
            bool is whether the chasing unit caught the target unit

        """
        reached_target: bool = False

        unit_path: List[Point2] = [start_position]
        target_idx = 0

        for i in range(100):
            next_position, reached_target = self._get_unit_next_position(
                current_position=unit_path[-1],
                current_target=target_unit_path[target_idx],
                distance_per_step=unit_speed,
            )
            unit_path.append(next_position)
            # keep updating the target index because we're chasing a moving target, but
            # stop if the unit we're chasing isn't moving any further
            target_idx = min(len(target_unit_path) - 1, target_idx + 1)

            if reached_target:
                # we caught the unit
                break

        return unit_path, reached_target
