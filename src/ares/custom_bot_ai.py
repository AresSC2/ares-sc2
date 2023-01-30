"""Extension of sc2.BotAI to add custom functions.

"""
from typing import Dict, Tuple

from consts import ALL_STRUCTURES
from dicts.unit_data import UNIT_DATA
from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId as UnitID
from sc2.position import Point2, Point3
from sc2.unit import Unit
from sc2.units import Units


class CustomBotAI(BotAI):
    """Extension of sc2.BotAI to add custom functions."""

    base_townhall_type: UnitID
    enemy_detectors: Units
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
