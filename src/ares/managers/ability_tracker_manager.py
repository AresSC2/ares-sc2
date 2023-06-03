"""Handle manual tracking of abilities until python-sc2 PR #163 is merged.

"""
from typing import TYPE_CHECKING, Dict, Optional

from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId as UnitID
from sc2.unit import Unit

from ares.consts import ManagerName, ManagerRequestType
from ares.dicts.ability_cooldowns import ABILITY_FRAME_COOL_DOWN
from ares.managers.manager import Manager
from ares.managers.manager_mediator import IManagerMediator, ManagerMediator

if TYPE_CHECKING:
    from ares import AresBot


class AbilityTrackerManager(Manager, IManagerMediator):
    """Manager to handle manually tracking abilities of units.

    Attributes
    ----------
    ability_frame_cd_dict : Dict[AbilityId, int]
        Dictionary with the cooldown of usable abilities for faster lookup.
    unit_to_ability_dict : Dict[int, Dict[AbilityId, int]]
        Dictionary of the unit tag to a dictionary of each Ability and when it was last
        used.

    """

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
            ManagerRequestType.GET_UNIT_TO_ABILITY_DICT: lambda kwargs: (
                self.unit_to_ability_dict
            ),
            ManagerRequestType.UPDATE_ABILITY_COOLDOWN: lambda kwargs: (
                self.update_ability_cooldown(**kwargs)
            ),
            ManagerRequestType.UPDATE_UNIT_TO_ABILITY_DICT: lambda kwargs: (
                self.update_unit_to_ability_dict(**kwargs)
            ),
        }
        # make a copy, so we don't mess with anything when updating Medivac cds
        self.ability_frame_cd_dict: Dict[
            AbilityId, int
        ] = ABILITY_FRAME_COOL_DOWN.copy()
        self.unit_to_ability_dict: Dict[int, Dict[AbilityId, int]] = dict()

    def manager_request(
        self,
        receiver: ManagerName,
        request: ManagerRequestType,
        reason: str = None,
        **kwargs
    ) -> Optional[Dict]:
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
        Optional[Dict] :
            Either one of the ability dictionaries is being returned or a function that
            returns None was called from a different manager (please don't do that).

        """
        return self.manager_requests_dict[request](kwargs)

    async def update(self, _iteration: int) -> None:
        """Not used by this manager.

        Manager is an abstract class and must have an ``update`` method.

        Parameters
        ----------
        _iteration :
            The current game iteration

        Returns
        -------

        """
        pass

    def catch_unit(self, unit: Unit) -> None:
        """Make sure units are included in the tracking.

        Notes
        -----
            Uncomment the code sections below for each unit as needed.

            Protoss:
                Carriers and Zealots are not included because their abilities start on
                autocast.
                Battery Overcharge and Strategic Recall (Nexus) are not included because
                they have global CDs.

        Parameters
        ----------
        unit :
            The Unit in question.

        Returns
        -------

        """
        tag: int = unit.tag
        unit_type: UnitID = unit.type_id
        current_frame: int = self.ai.state.game_loop
        if tag not in self.unit_to_ability_dict:
            if unit_type == UnitID.WIDOWMINE:
                self.unit_to_ability_dict[tag] = {
                    AbilityId.WIDOWMINEATTACK_WIDOWMINEATTACK: current_frame
                }
            # Protoss
            # if unit_type == UnitID.ADEPT:
            #     self.unit_to_ability_dict[tag] = {
            #         AbilityId.ADEPTPHASESHIFT_ADEPTPHASESHIFT: current_frame
            #     }
            # elif unit_type == UnitID.DARKTEMPLAR:
            #     self.unit_to_ability_dict[tag] = {
            #         AbilityId.EFFECT_SHADOWSTRIDE: current_frame
            #     }
            # elif unit_type == UnitID.DISRUPTOR:
            #     self.unit_to_ability_dict[tag] = {
            #         AbilityId.EFFECT_PURIFICATIONNOVA: current_frame
            #     }
            # elif unit_type == UnitID.ORACLE:
            #     self.unit_to_ability_dict[tag] = {
            #         AbilityId.BEHAVIOR_PULSARBEAMON: current_frame,
            #         AbilityId.ORACLEREVELATION_ORACLEREVELATION: current_frame,
            #     }
            # elif unit_type == UnitID.STALKER:
            #     self.unit_to_ability_dict[tag] = {
            #         AbilityId.EFFECT_BLINK_STALKER: current_frame
            #     }
            # elif unit_type == UnitID.VOIDRAY:
            #     self.unit_to_ability_dict[tag] = {
            #         AbilityId.EFFECT_VOIDRAYPRISMATICALIGNMENT: current_frame
            #     }

            # Terran
            # elif unit_type == UnitID.BATTLECRUISER:
            #     self.unit_to_ability_dict[tag] = {
            #         AbilityId.EFFECT_TACTICALJUMP: current_frame,
            #         AbilityId.YAMATO_YAMATOGUN: current_frame,
            #     }
            # elif unit_type == UnitID.CYCLONE:
            #     self.unit_to_ability_dict[tag] = {
            #         AbilityId.LOCKON_LOCKON: current_frame,
            #     }
            # elif unit_type == UnitID.GHOST:
            #     self.unit_to_ability_dict[tag] = {
            #         AbilityId.TACNUKESTRIKE_NUKECALLDOWN: current_frame,
            #     }
            # elif unit_type == UnitID.MEDIVAC:
            #     self.unit_to_ability_dict[tag] = {
            #         AbilityId.EFFECT_MEDIVACIGNITEAFTERBURNERS: current_frame,
            #     }
            # elif unit_type == UnitID.REAPER:
            #     self.unit_to_ability_dict[tag] = {
            #         AbilityId.KD8CHARGE_KD8CHARGE: current_frame
            #     }

            # Zerg
            # elif unit_type == UnitID.CORRUPTOR:
            #     self.unit_to_ability_dict[tag] = {
            #         AbilityId.CAUSTICSPRAY_CAUSTICSPRAY: current_frame
            #     }
            # elif unit_type in {UnitID.SWARMHOSTMP, UnitID.SWARMHOSTBURROWEDMP}:
            #     self.unit_to_ability_dict[tag] = {
            #         AbilityId.EFFECT_SPAWNLOCUSTS: current_frame
            #     }
            # elif unit_type == UnitID.RAVAGER:
            #     self.unit_to_ability_dict[tag] = {
            #         AbilityId.EFFECT_CORROSIVEBILE: current_frame
            #     }

    def update_ability_cooldown(
        self, ability: AbilityId, new_cd_in_seconds: float, frame_offset: int = 6
    ) -> None:
        """Update the ability cooldown in the duration dictionary.

        Use this if the cd is no longer the base CD, i.e. after Rapid Reignition System
        is researched for Medivacs.

        Parameters
        ----------
        ability :
            The AbilityId to update
        new_cd_in_seconds :
            How long the new cooldown is
        frame_offset :
            Any additional offset frames to ensure abilities will be ready

        Returns
        -------

        """
        self.ability_frame_cd_dict[ability] = (
            int(22.4 * new_cd_in_seconds) + frame_offset
        )

    def update_unit_to_ability_dict(self, ability: AbilityId, unit_tag: int) -> None:
        """Update tracking to reflect ability usage.

        After a unit uses an ability it should call this to update the frame the
        ability will next be available

        Parameters
        ----------
        ability :
            The AbilityId that was used.
        unit_tag :
            The tag of the Unit that used the ability

        Returns
        -------

        """
        current_frame: int = self.ai.state.game_loop
        if unit_tag in self.unit_to_ability_dict:
            self.unit_to_ability_dict[unit_tag][ability] = (
                current_frame + self.ability_frame_cd_dict[ability]
            )
