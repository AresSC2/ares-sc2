"""Extension of sc2.BotAI to add custom functions.

"""
import math
from typing import Dict, List, Tuple

from loguru import logger
from sc2.bot_ai import BotAI
from sc2.constants import EQUIVALENTS_FOR_TECH_PROGRESS
from sc2.ids.unit_typeid import UnitTypeId as UnitID
from sc2.position import Point2, Point3
from sc2.unit import Unit
from sc2.units import Units

from ares.consts import ALL_STRUCTURES
from ares.dicts.turn_rate import TURN_RATE
from ares.dicts.unit_data import UNIT_DATA
from ares.dicts.unit_tech_requirement import UNIT_TECH_REQUIREMENT


class CustomBotAI(BotAI):
    """Extension of sc2.BotAI to add custom functions."""

    base_townhall_type: UnitID
    enemy_detectors: Units
    enemy_parasitic_bomb_positions: List[Point2]
    gas_type: UnitID
    unit_tag_dict: Dict[int, Unit]
    worker_type: UnitID

    async def on_step(self, iteration: int):
        """Here because all abstract methods have to be implemented.

        Gets overridden in Ares.

        Parameters
        ----------
        iteration :
            The current game iteration

        Returns
        -------

        """
        pass

    def draw_text_on_world(
        self,
        pos: Point2,
        text: str,
        size: int = 12,
        y_offset: int = 0,
        color=(0, 255, 255),
    ) -> None:
        """Print out text to the game screen.

        Parameters
        ----------
        pos :
            Where the text should be drawn.
        text :
            What text to draw.
        size :
            How large the text should be.
        y_offset :
            How far offset the text should be along the y-axis to ensure visibility of
            both text and whatever the text is describing.
        color :
            What color the text should be.

        Returns
        -------

        """
        z_height: float = self.get_terrain_z_height(pos)
        self.client.debug_text_world(
            text,
            Point3((pos.x, pos.y + y_offset, z_height)),
            color=color,
            size=size,
        )

    @staticmethod
    def get_total_supply(units: Units) -> int:
        """Get total supply of units.

        Parameters
        ----------
        units :
            Units object to return the total supply of

        Returns
        -------
        int :
            The total supply of the Units object.

        """
        return sum(
            [
                UNIT_DATA[unit.type_id]["supply"]
                for unit in units
                # yes we did have a crash getting supply of a nuke!
                if unit.type_id not in ALL_STRUCTURES and unit.type_id != UnitID.NUKE
            ]
        )

    def split_ground_fliers(self, units: Units) -> Tuple[Units, Units]:
        """Split units into ground units and flying units.

        Parameters
        ----------
        units :
            Units object that should be split

        Returns
        -------
        Tuple[Units, Units] :
            Tuple where the first element is the ground units present in `Units` and
            the second element is the flying units present in `Units`

        """
        ground, fly = [], []
        for unit in units:
            if unit.is_flying:
                fly.append(unit)
            else:
                ground.append(unit)
        return Units(ground, self), Units(fly, self)

    def attack_ready(self, unit: Unit, target: Unit) -> bool:
        """Check if the unit is ready to attack.

        Considers whether the unit can attack the target by the time the unit faces the
        target.

        Thanks, Sasha, for writing this out.

        """
        # fix for units, where this method returns False so the unit moves
        # but the attack animation is still active, so the move command cancels the
        # attack need to think of a better fix later, but this is better than a unit not
        # attacking and still better than using simple weapon.cooldown == 0 micro
        if unit.weapon_cooldown > 7 and unit.type_id == UnitID.HYDRALISK:
            return True
        # prevents crash, since unit can't move
        if unit.type_id == UnitID.LURKERMPBURROWED:
            return True
        if not unit.can_attack:
            return False
        # Time elapsed per game step
        step_time: float = self.client.game_step / 22.4

        # Time it will take for unit to turn to face target
        angle: float = self.angle_diff(
            unit.facing, self.angle_to(unit.position, target.position)
        )
        turn_time: float = angle / self.get_turn_speed(unit)

        # Time it will take for unit to move in range of target
        distance = (
            unit.distance_to(target)
            - unit.radius
            - target.radius
            - self.range_vs_target(unit, target)
        )
        distance = max(0, distance)
        move_time = distance / ((unit.real_speed + 1e-16) * 1.4)

        return step_time + turn_time + move_time >= unit.weapon_cooldown / 22.4

    def tech_ready_for_unit(self, unit_type: UnitID) -> bool:
        """
        Similar to python-sc2's `tech_requirement_progress` but this one specializes
        in units and simply returns a boolean.
        Since tech_requirement_progress is not reliable for non-structures.

        Parameters
        ----------
        unit_type :
            Unit type id we want to check if tech is ready for.

        Returns
        -------
        bool :
            Indicating tech is ready.
        """
        if unit_type not in UNIT_TECH_REQUIREMENT:
            logger.warning(f"{unit_type} not in UNIT_TECH_REQUIREMENT dictionary")
            return True

        tech_buildings_required: set[UnitID] = UNIT_TECH_REQUIREMENT[unit_type]

        for tech_building_id in tech_buildings_required:
            to_check = [tech_building_id]
            # check for alternatives structures
            # for example gateway might be a requirement, but we might have warpgates
            if tech_building_id in EQUIVALENTS_FOR_TECH_PROGRESS:
                to_check.append(
                    next(iter(EQUIVALENTS_FOR_TECH_PROGRESS[tech_building_id]))
                )

            if not any(
                [
                    s
                    for s in self.structures
                    if s.type_id == tech_building_id and s.is_ready
                ]
            ):
                return False

        return True

    @staticmethod
    def angle_diff(a, b) -> float:
        """Absolute angle difference between 2 angles.

        Parameters
        ----------
        a :
            Angle 1.
        b :
            Angle 2.

        Returns
        -------
        float :
            Absolute angle difference between 2 angles.

        """
        if a < 0:
            a += math.pi * 2
        if b < 0:
            b += math.pi * 2
        return math.fabs(a - b)

    @staticmethod
    def angle_to(from_pos: Point2, to_pos: Point2) -> float:
        """Angle from point to other point in radians.

        Parameters
        ----------
        from_pos :
            Start position.
        to_pos :
            Target position.

        Returns
        -------
        float :
            Angle from `from_pos` to `to_pos`.

        """
        return math.atan2(to_pos.y - from_pos.y, to_pos.x - to_pos.x)

    @staticmethod
    def get_turn_speed(unit) -> float:
        """Returns turn speed of unit in radians per second.

        Parameters
        ----------
        unit :
            Unit to get the turn rate of.

        Returns
        -------
            float :
                Turn rate of the unit.

        """
        if unit.type_id in TURN_RATE:
            return TURN_RATE[unit.type_id] * 1.4 * math.pi / 180

    @staticmethod
    def range_vs_target(unit, target) -> float:
        """Get the range of a unit to a target.

        Parameters
        ----------
        unit :
            Unit to get the range of.
        target :
            Target the unit wants to attack.

        Returns
        -------
        float :
            Range of the unit vs the target.

        """
        if unit.can_attack_air and target.is_flying:
            return unit.air_range
        else:
            return unit.ground_range
