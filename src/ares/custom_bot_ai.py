"""Extension of sc2.BotAI to add custom functions.

"""
from typing import Dict, List, Optional, Tuple, Union

from cython_extensions import cy_distance_to_squared
from loguru import logger
from s2clientprotocol import raw_pb2 as raw_pb
from s2clientprotocol import sc2api_pb2 as sc_pb
from s2clientprotocol import ui_pb2 as ui_pb
from sc2.bot_ai import BotAI
from sc2.constants import EQUIVALENTS_FOR_TECH_PROGRESS
from sc2.dicts.upgrade_researched_from import UPGRADE_RESEARCHED_FROM
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId as UnitID
from sc2.ids.upgrade_id import UpgradeId
from sc2.position import Point2, Point3
from sc2.unit import Unit
from sc2.units import Units

from ares.consts import ALL_STRUCTURES, ID, TARGET
from ares.dicts.unit_data import UNIT_DATA
from ares.dicts.unit_tech_requirement import UNIT_TECH_REQUIREMENT
from ares.managers.manager_mediator import ManagerMediator


class CustomBotAI(BotAI):
    """Extension of sc2.BotAI to add custom functions."""

    base_townhall_type: UnitID
    enemy_detectors: Units
    enemy_parasitic_bomb_positions: List[Point2]
    gas_type: UnitID
    unit_tag_dict: Dict[int, Unit]
    worker_type: UnitID
    mediator: ManagerMediator

    async def on_step(self, iteration: int):  # pragma: no cover
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
    ) -> None:  # pragma: no cover
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
    def get_total_supply(units: Union[Units, list[Unit]]) -> int:
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

    def not_started_but_in_building_tracker(self, structure_type: UnitID) -> bool:
        """
        Figures out if worker in on route to build something, and
        that structure_type doesn't exist yet.

        Parameters
        ----------
        structure_type

        Returns
        -------

        """
        building_tracker: dict = self.mediator.get_building_tracker_dict
        for tag, info in building_tracker.items():
            structure_id: UnitID = building_tracker[tag][ID]
            if structure_id != structure_type:
                continue

            target: Point2 = building_tracker[tag][TARGET]

            if not self.structures.filter(
                lambda s: cy_distance_to_squared(s.position, target.position) < 1.0
            ):
                return True

        return False

    def pending_or_complete_upgrade(self, upgrade_id: UpgradeId) -> bool:
        if upgrade_id in self.state.upgrades:
            return True

        creationAbilityID = self.game_data.upgrades[
            upgrade_id.value
        ].research_ability.exact_id

        researched_from: UnitID = UPGRADE_RESEARCHED_FROM[upgrade_id]
        upgrade_from_structures: Units = self.mediator.get_own_structures_dict[
            researched_from
        ]

        for structure in upgrade_from_structures:
            for order in structure.orders:
                if order.ability.exact_id == creationAbilityID:
                    return True

        return False

    def split_ground_fliers(
        self, units: Union[Units, list[Unit]], return_as_lists: bool = False
    ) -> Union[Tuple[Units, Units], Tuple[list, list]]:
        """Split units into ground units and flying units.

        Parameters
        ----------
        units :
            Units object that should be split
        return_as_lists :
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
        if return_as_lists:
            return ground, fly
        else:
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
                [s for s in self.structures if s.type_id in to_check and s.is_ready]
            ):
                return False

        return True

    async def _give_units_same_order(
        self,
        order: AbilityId,
        unit_tags: Union[List[int], set[int]],
        target: Optional[Union[Point2, Unit, int]] = None,
    ) -> None:  # pragma: no cover
        """
        Give units corresponding to the given tags the same order.
        @param order: the order to give to all units
        @param unit_tags: the tags of the units to give the order to
        @param target: either a Point2 of the location or the tag of the unit to target
        """
        if not target:
            # noinspection PyProtectedMember
            await self.client._execute(
                action=sc_pb.RequestAction(
                    actions=[
                        sc_pb.Action(
                            action_raw=raw_pb.ActionRaw(
                                unit_command=raw_pb.ActionRawUnitCommand(
                                    ability_id=order.value,
                                    unit_tags=unit_tags,
                                )
                            )
                        ),
                    ]
                )
            )
        elif isinstance(target, Point2):
            # noinspection PyProtectedMember
            await self.client._execute(
                action=sc_pb.RequestAction(
                    actions=[
                        sc_pb.Action(
                            action_raw=raw_pb.ActionRaw(
                                unit_command=raw_pb.ActionRawUnitCommand(
                                    ability_id=order.value,
                                    target_world_space_pos=target.as_Point2D,
                                    unit_tags=unit_tags,
                                )
                            )
                        ),
                    ]
                )
            )
        else:
            tag: int
            if isinstance(target, Unit):
                tag = target.tag
            elif isinstance(target, int):
                tag = target
            else:
                logger.warning(
                    f"Got {target} argument, and not sure what to do with it. "
                    f" `_give_units_same_order` will not execute."
                )
                return

            # noinspection PyProtectedMember
            await self.client._execute(
                action=sc_pb.RequestAction(
                    actions=[
                        sc_pb.Action(
                            action_raw=raw_pb.ActionRaw(
                                unit_command=raw_pb.ActionRawUnitCommand(
                                    ability_id=order.value,
                                    target_unit_tag=tag,
                                    unit_tags=unit_tags,
                                )
                            )
                        ),
                    ]
                )
            )

    async def _do_archon_morph(self, templar: list[Unit]) -> None:  # pragma: no cover
        command = raw_pb.ActionRawUnitCommand(
            ability_id=AbilityId.MORPH_ARCHON.value,
            unit_tags=[templar[0].tag, templar[1].tag],
            queue_command=False,
        )
        action = raw_pb.ActionRaw(unit_command=command)
        await self.client._execute(
            action=sc_pb.RequestAction(actions=[sc_pb.Action(action_raw=action)])
        )

    async def unload_by_tag(
        self, container: Unit, unit_tag: int
    ) -> None:  # pragma: no cover
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

    async def unload_container(
        self, container_tag: int, index: int = 0
    ) -> None:  # pragma: no cover
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
        dist: float = distance**2
        return [
            s
            for s in self.enemy_structures
            if cy_distance_to_squared(s.position, from_position) < dist
        ]
