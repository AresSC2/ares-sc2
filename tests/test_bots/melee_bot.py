import random
import sys
from os.path import abspath, dirname, join

import numpy as np
from sc2 import maps
from sc2.ids.unit_typeid import UnitTypeId
from sc2.main import run_game
from sc2.position import Point2
from sc2.unit import Unit

# Get the directory of the current file
current_dir = dirname(__file__)

# Go two directories up
two_up = abspath(join(current_dir, "..", ".."))

# Append the src folder to the path
src_path = join(two_up, "src")

# Add the src folder to the system path
sys.path.append(src_path)

from sc2.data import Difficulty, Race
from sc2.player import Bot, Computer

from ares import AresBot
from ares.behaviors.combat import CombatManeuver
from ares.behaviors.combat.individual import AMove, PathUnitToTarget
from ares.behaviors.macro import (
    AutoSupply,
    BuildWorkers,
    ExpansionController,
    GasBuildingController,
    MacroPlan,
    Mining,
    ProductionController,
    SpawnController,
)


class DummyBot(AresBot):
    def __init__(self):
        super().__init__()

    @property
    def army_comp(self) -> dict:
        if self.race == Race.Protoss:
            return {
                UnitTypeId.OBSERVER: {"proportion": 0.01, "priority": 0},
                UnitTypeId.IMMORTAL: {"proportion": 0.09, "priority": 1},
                UnitTypeId.STALKER: {"proportion": 0.9, "priority": 2},
            }
        elif self.race == Race.Terran:
            return {
                UnitTypeId.MEDIVAC: {"proportion": 0.01, "priority": 0},
                UnitTypeId.MARAUDER: {"proportion": 0.09, "priority": 1},
                UnitTypeId.MARINE: {"proportion": 0.9, "priority": 2},
            }
        else:
            return {
                UnitTypeId.MUTALISK: {"proportion": 0.1, "priority": 2},
                UnitTypeId.BANELING: {"proportion": 0.2, "priority": 1},
                UnitTypeId.ZERGLING: {"proportion": 0.7, "priority": 0},
            }

    async def on_step(self, iteration: int):
        await super(DummyBot, self).on_step(iteration)

        # while here test out some macro and combat behaviors
        self.register_behavior(Mining())
        macro_plan: MacroPlan = MacroPlan()
        macro_plan.add(AutoSupply(base_location=self.start_location))
        macro_plan.add(BuildWorkers(100))
        macro_plan.add(ExpansionController(to_count=4, max_pending=1))
        macro_plan.add(
            GasBuildingController(
                to_count=100,
                max_pending=100,
            )
        )
        if self.race != Race.Zerg:
            macro_plan.add(ProductionController(self.army_comp, self.start_location))
        macro_plan.add(SpawnController(self.army_comp))
        self.register_behavior(macro_plan)

        army: list[Unit] = [u for u in self.units if u.type_id != self.worker_type]
        grid: np.ndarray = self.mediator.get_ground_grid
        target: Point2 = self.enemy_start_locations[0]
        if self.enemy_structures:
            target = self.enemy_structures[0].position

        for unit in army:
            maneuver: CombatManeuver = CombatManeuver()
            maneuver.add(
                PathUnitToTarget(
                    unit=unit, grid=grid, target=target, success_at_distance=10.0
                )
            )
            maneuver.add(AMove(unit=unit, target=target))
            self.register_behavior(maneuver)

    async def on_start(self) -> None:
        await super(DummyBot, self).on_start()

        desired_army = {
            Race.Protoss: [UnitTypeId.STALKER, UnitTypeId.IMMORTAL, UnitTypeId.VOIDRAY],
            Race.Terran: [UnitTypeId.MARINE, UnitTypeId.MARAUDER, UnitTypeId.MEDIVAC],
            Race.Zerg: [UnitTypeId.ROACH, UnitTypeId.HYDRALISK, UnitTypeId.MUTALISK],
        }

        await self.client.debug_create_unit(
            [[self.worker_type, 30, self.start_location, 1]]
        )

        await self.client.debug_create_unit(
            [
                [unit_type, 8, self.start_location, 1]
                for unit_type in desired_army[self.race]
            ]
        )


# Start game
if __name__ == "__main__":
    random_map = random.choice(
        [
            "Equilibrium513AIE",
            "Gresvan513AIE",
            "GoldenAura513AIE",
            "HardLead513AIE",
            "Oceanborn513AIE",
            "SiteDelta513AIE",
        ]
    )
    run_game(
        maps.get(random_map),
        [
            Bot(Race.Random, DummyBot(), "DummyBot"),
            Computer(Race.Protoss, Difficulty.CheatInsane),
        ],
        realtime=False,
    )
