from typing import Tuple

from .sc2_helper import CombatPredictor, CombatSettings


class CombatSimulator:
    def __init__(self):
        self.combat_predictor: CombatPredictor = CombatPredictor()
        self.combat_settings: CombatSettings = CombatSettings()

    def debug(self, value: bool):
        """
        Print debug information. Warning: Slow!
        Do not enable in production.

        Default: False
        :param value:
        :return:
        """
        self.combat_settings.debug = value

    def bad_micro(self, value: bool):
        """
        Set value of bad_micro for CombatSettings.

        Default: False
        :param value:
        :return:
        """
        self.combat_settings.bad_micro = value

    def enable_splash(self, value: bool):
        """
        TODO: Implement splash damage in combat simulator.

        Default: True
        :param value:
        :return:
        """
        self.combat_settings.enable_splash = value

    def enable_timing_adjustment(self, value: bool):
        """
        Take distance between units into account.

        Default: False

        :param value:
        :return:
        """
        self.combat_settings.enable_timing_adjustment = value

    def enable_surround_limits(self, value: bool):
        """
        Enable surround limits for melee units, i.e. only a
        few units can attack a marine at a time

        Default: True
        :param value:
        :return:
        """
        self.combat_settings.enable_surround_limits = value

    def enable_melee_blocking(self, value: bool):
        """
        Melee units blocking each other

        Default: True
        :param value:
        :return:
        """
        self.combat_settings.enable_melee_blocking = value

    def workers_do_no_damage(self, value: bool):
        """
        Don't take workers into account.

        Default: False
        :param value:
        :return:
        """
        self.combat_settings.workers_do_no_damage = value

    def assume_reasonable_positioning(self, value):
        """
        Assume units are decently split.

        Default: True
        :param value:
        :return:
        """
        self.combat_settings.assume_reasonable_positioning = value

    def max_time(self, value: float):
        """
        Max game time to spend in simulation

        Default: 100 000.00
        :param value:
        :return:
        """
        self.combat_settings.max_time = value

    def start_time(self, value: float):
        """
        Start time of simulation. No used yet, will be used for Buffs
        Default: 0.0
        :param value:
        :return:
        """
        self.combat_settings.start_time = value

    def predict_engage(
        self, own_units, enemy_units, optimistic: bool = False, defender_player: int = 0
    ) -> Tuple[bool, float]:
        """
        Predict an engagement between two sets of units and returns a tuple containing Winner(True if own_units won)
        and winner's units' health left after engagement.

        :param own_units: sc2.Units object containing own units to simulate
        :param enemy_units: sc2.Units object containing enemy units to simulate
        :param optimistic: This controls who fires first. If optimistic == True - own_units fire first else enemy_units
        fire first.
        :param defender_player: Defending player. 1 == Self, 2 == Enemy
        :return:
        """
        if optimistic:

            winner, health_left = self.combat_predictor.predict_engage(
                own_units, enemy_units, defender_player, self.combat_settings
            )
            if winner == 1:
                return True, health_left
            else:
                return False, health_left
        else:
            if defender_player == 1:
                defender_player = 2
            elif defender_player == 2:
                defender_player = 1

            winner, health_left = self.combat_predictor.predict_engage(
                enemy_units, own_units, defender_player, self.combat_settings
            )
            if winner == 2:
                return True, health_left
            else:
                return False, health_left
