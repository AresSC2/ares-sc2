Combat Behaviors serve as essential components for constructing intricate unit and group control strategies. 
These behaviors act as modular elements that can be combined to create bespoke combat maneuvers. 
To facilitate the process of creating army behaviors, a practical aid called the `CombatManeuver` helper 
class is made available.

To illustrate the concept, consider the following example that demonstrates the execution of a mine drop:
```python
from ares import AresBot
from ares.behaviors.combat import CombatManeuver
from ares.behaviors.combat.individual import (
    DropCargo,
    KeepUnitSafe,
    PathUnitToTarget,
    PickUpCargo,
)
from sc2.unit import Unit
from sc2.units import Units
import numpy as np

class MyBot(AresBot):
    async def on_step(self, iteration: int) -> None:
        # retrieve medivac and mines_to_pickup and pass to method
        # left out here for clarity
        # mines would require their own behavior
        self.do_medivac_mine_drop(medivac, mines_to_pickup)
        
    def do_medivac_mine_drop(
            self, 
            medivac: Unit, 
            mines_to_pickup: Units
    ) -> None:
        # initialize a new CombatManeuver
        mine_drop: CombatManeuver = CombatManeuver()
        # get a grid for the medivac to path on
        air_grid: np.ndarray = self.mediator.get_air_grid
        # first priority is picking up units
        mine_drop.add(
            PickUpCargo(
                unit=medivac, 
                grid=air_grid, 
                pickup_targets=mines_to_pickup)
        )
        # if there is cargo, path to target and drop them off
        if medivac.has_cargo:
            # path
            mine_drop.add(
                PathUnitToTarget(
                    unit=medivac,
                    grid=air_grid,
                    target=self.enemy_start_locations[0],
                )
            )
            # drop off the mines
            mine_drop.add(
                DropCargo(unit=medivac, target=medivac.position)
            )
        # no cargo and no units to pick up, stay safe
        else:
            mine_drop.add(
                KeepUnitSafe(unit=medivac, grid=air_grid)
            )
        
        # finally register this maneuver to be executed
        self.register_behavior(mine_drop)
```

Combat Behaviors can also be executed individually if required:
```python
self.register_behavior(KeepUnitSafe(unit=medivac, grid=air_grid))
```
