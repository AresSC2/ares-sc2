"""Extension of sc2.BotAI to add custom functions.

"""
from typing import Dict, List, Tuple

from loguru import logger
from s2clientprotocol import raw_pb2 as raw_pb
from s2clientprotocol import sc2api_pb2 as sc_pb
from s2clientprotocol import ui_pb2 as ui_pb
from sc2.bot_ai import BotAI
from sc2.constants import EQUIVALENTS_FOR_TECH_PROGRESS
from sc2.ids.unit_typeid import UnitTypeId as UnitID
from sc2.position import Point2, Point3
from sc2.unit import Unit
from sc2.units import Units

from ares.consts import ALL_STRUCTURES
from ares.cython_extensions.geometry import cy_distance_to
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

    async def unload_by_tag(self, container: Unit, unit_tag: int) -> None:
        """Unload a unit from a container based on its tag. Thanks, Sasha!"""
        index: int = 0
        # noinspection PyProtectedMember
        if not container._proto.passengers:
            return
        # noinspection PyProtectedMember
        for index, passenger in enumerate(container._proto.passengers):
            if passenger.tag == unit_tag:
                break
            # noinspection PyProtectedMember
            if index == len(container._proto.passengers) - 1:
                logger.warning(f"Can't find passenger {unit_tag}")
                return

        await self.unload_container(container, index)

    async def unload_container(self, container_tag: int, index: int = 0) -> None:
        # noinspection PyProtectedMember
        await self.client._execute(
            action=sc_pb.RequestAction(
                actions=[
                    sc_pb.Action(
                        action_raw=raw_pb.ActionRaw(
                            unit_command=raw_pb.ActionRawUnitCommand(
                                ability_id=0, unit_tags=[container_tag]
                            )
                        )
                    ),
                    sc_pb.Action(
                        action_ui=ui_pb.ActionUI(
                            cargo_panel=ui_pb.ActionCargoPanelUnload(unit_index=index)
                        )
                    ),
                ]
            )
        )

    def get_enemy_proxies(
        self,
        distance: float,
        from_position: Point2,
    ) -> list[Unit]:
        return [
            s
            for s in self.enemy_structures
            if cy_distance_to(s.position, from_position) < distance
        ]
