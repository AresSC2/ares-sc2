from time import perf_counter_ns

from sc2 import BotAI, Difficulty, Race, UnitTypeId, maps, run_game
from sc2.player import Bot, Computer

from sc2_helper import CombatPredictor, CombatSettings, test_unit, test_units


class basic_bot(BotAI):
    def __init__(self):
        super().__init__()

    async def on_step(self, iteration):
        self.single = 0
        self.double = 0
        if iteration == 0:
            # await self.client.debug_show_map()
            self.combat_predictor = CombatPredictor()
            self.combat_settings = CombatSettings()
            self.combat_settings.debug = True
            await self.client.debug_create_unit(
                [[UnitTypeId.MARINE, 10, self.start_location, 1]]
            )
            await self.client.debug_create_unit(
                [[UnitTypeId.BATTLECRUISER, 10, self.start_location, 2]]
            )
            # await self.client.debug_create_unit([[UnitTypeId.TEMPEST, 10, self.start_location, 2]])
            # await self.client.debug_upgrade()
        if self.units(UnitTypeId.MARINE):
            zergling = self.enemy_units(UnitTypeId.BATTLECRUISER)[0]
            # s = perf_counter_ns()
            test_unit(zergling)
            await self.client.leave()
            # e = perf_counter_ns()
            # t = e - s
            # print(t)
            # self.single += t
            # zerglings = self.units().filter(lambda x: x.type_id == UnitTypeId.ZERGLING)
            # s = perf_counter_ns()
            # test_units(zerglings)
            # e = perf_counter_ns()
            # t = e-s
            # print(t)
            # self.double += t
            print(
                self.combat_predictor.predict_engage(
                    self.units, self.enemy_units, 1, self.combat_settings
                )
            )
        if iteration > 10:
            # print(self.single/(iteration-1))
            # print(self.double/(iteration-1))
            await self.client.leave()


if __name__ == "__main__":
    run_game(
        maps.get("DiscoBloodbathLE"),
        [
            Bot(Race.Terran, basic_bot()),
            Computer(Race.Protoss, Difficulty.CheatInsane),
        ],
        realtime=False,
    )
