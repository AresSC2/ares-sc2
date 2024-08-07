"""Various useful methods for using in game chat to send debug commands.

Feel free to add to this.
"""

from sc2.ids.unit_typeid import UnitTypeId as UnitID
from sc2.position import Point2
from sc2.units import Units

from ares.consts import (
    COOLDOWN,
    CREATE,
    FOOD,
    GOD,
    KILL,
    RESOURCES,
    SHOW_MAP,
    TECH_TREE,
    UPGRADES,
)
from ares.custom_bot_ai import CustomBotAI


class ChatDebug:
    """Class for handling in-game chat and sending the appropriate debug commands
    to the client.
    """

    def __init__(self, ai: CustomBotAI):
        """Set `CustomBotAI` that should be sending the commands.

        Parameters
        ----------
        ai
        """
        self.ai: CustomBotAI = ai

    async def parse_commands(self) -> None:  # pragma: no cover
        """Read chat since last iteration and send debug command if it matches.

        Returns
        -------

        """
        messages = self.ai.state.chat
        if len(messages) > 0:
            chat = messages[0].message.upper()
            commands = chat.split()
            first_command: str = commands[0].upper()

            if first_command in KILL:
                if len(commands) < 3:
                    await self.ai.chat_send("Not a valid command")
                    return
                if commands[2].upper() not in UnitID.__members__:
                    await self.ai.chat_send("Not a valid UnitID, try again")
                    return
                # example chat command
                # kill 1 overseers
                if len(commands) >= 3:
                    await self._destroy_units(
                        int(commands[1]), UnitID[commands[2].upper()]
                    )
                # example chat command
                # kill 1 overseers 2
                if len(commands) >= 4:
                    await self._destroy_units(
                        int(commands[1]), UnitID[commands[2].upper()], int(commands[3])
                    )

                if len(commands) >= 2:
                    # TODO: This can be to kill a unit by tag, for example:
                    #   kill 48025168
                    pass

            if first_command in CREATE:
                if len(commands) < 3:
                    await self.ai.chat_send("Not a valid command")
                    return
                # check for valid unit id
                if commands[2].upper() not in UnitID.__members__:
                    await self.ai.chat_send("Not a valid UnitID, try again")
                    return
                # example chat command, by default creates for player 1
                # create 10 overseer
                if len(commands) == 3:
                    await self._create_units(
                        int(commands[1]), UnitID[commands[2].upper()]
                    )
                # example chat command, last element is player id
                # create 10 overseer 2
                if len(commands) == 4:
                    await self._create_units(
                        int(commands[1]), UnitID[commands[2].upper()], int(commands[3])
                    )

            if first_command in COOLDOWN:
                await self.ai.client.debug_cooldown()

            if first_command in FOOD:
                await self.ai.client.debug_food()

            if first_command in GOD:
                await self.ai.client.debug_god()

            if first_command in RESOURCES:
                await self.ai.client.debug_all_resources()

            if first_command in SHOW_MAP:
                await self.ai.client.debug_show_map()

            if first_command in TECH_TREE:
                await self.ai.client.debug_tech_tree()

            if first_command in UPGRADES:
                await self.ai.client.debug_upgrade()

    async def _create_units(
        self,
        amount: int,
        unit_id: UnitID,
        player_id: int = 1,
    ) -> None:  # pragma: no cover
        """Create units at player camera location.

        Parameters
        ----------
        amount :
            Number of units to create
        unit_id :
            What type of unit to create
        player_id :
            Which player should be controlling the unit

        Returns
        -------

        """

        player_camera = self.ai.state.observation_raw.player.camera
        pos = Point2((player_camera.x, player_camera.y))
        await self.ai.client.debug_create_unit([[unit_id, amount, pos, player_id]])

    async def _destroy_units(
        self, num_to_destroy: int, unit_id: UnitID, player_id: int = 1
    ) -> None:  # pragma: no cover
        """Destroy units for provided player.

        Parameters
        ----------
        num_to_destroy :
            How many units to destroy
        unit_id :
            What type of unit to destroy
        player_id :
            Which player the destroyed units should belong to

        Returns
        -------

        """
        if player_id == 1:
            units_to_destroy: Units = self.ai.all_own_units(unit_id)
        else:
            units_to_destroy: Units = self.ai.all_enemy_units(unit_id)

        if not units_to_destroy:
            await self.ai.chat_send("Can't find any of those")
            return

        must_die: Units = units_to_destroy.take(num_to_destroy)

        await self.ai.client.debug_kill_unit(must_die.tags)
