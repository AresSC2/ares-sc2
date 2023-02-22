"""Debug spawn units at the beginning of the game.

"""
from custom_bot_ai import CustomBotAI
from sc2.position import Point2


class DebugSpawn:
    """Class for managing the debug spawning of units via the client."""

    def __init__(self, ai: CustomBotAI):
        """Set up CustomBotAI for spawning.

        Parameters
        ----------
        ai :
            The CustomBotAI object that should spawn units
        """
        self.ai: CustomBotAI = ai

    async def spawn(
        self, enemy_nat: Point2, own_nat: Point2, enemy_third: Point2
    ) -> None:
        """
        Spawn units to create test scenarios at the beginning of the game.

        (remember to turn off in config before uploading !!!)
        TODO: ladder script generates production config file

        Parameters
        ----------
        enemy_nat :
            Position of the enemy natural base
        own_nat :
            Position of own natural base
        enemy_third :
            Position of the enemy third base

        Returns
        -------

        """

        pass
