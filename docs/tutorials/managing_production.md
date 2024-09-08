
Dealing with production logic for a bot often means wrestling with the same old repetitive code headaches. 
Imagine starting off with a bot geared towards a stalker and immortal combo, finely tuning your logic around
that. Now, say you want to shake things up and switch to a late-game skytoss setup – suddenly, you're 
stuck adding more code for production facilities, tech structures, and handling those late-game units.

We get it, this kind of redundancy is a pain. We didn't just 
want to make transitioning between army compositions smoother; we wanted to kick out all that extra, 
unnecessary code clutter. Whether you're rocking a stalker and immortal crew or going all-in on a late-game 
skytoss spectacle, our approach offers a more straightforward and adaptable development process.

Furthermore, this system is split into two main behaviors, the `SpawnController` to manage army production,
and `ProductionController` to add production and tech up. Depending on your needs you can use one, both or
none at all!

## Defining army compositions
Both controllers rely on an army composition dictionary, for example:
```python
from sc2.ids.unit_typeid import UnitTypeId as UnitID

@property
def viking_tank(self) -> dict:
    return {
        UnitID.MARINE: {"proportion": 0.69, "priority": 4},
        UnitID.SIEGETANK: {"proportion": 0.13, "priority": 0},
        UnitID.VIKINGFIGHTER: {"proportion": 0.16, "priority": 3},
        UnitID.RAVEN: {"proportion": 0.02, "priority": 1},
    }

```
Things to note:

 - `SpawnController` will not produce build structures for you. Please be especially careful
of this fact when morphing units. For example Archons, Banelings, Ravagers, Lurkers or Brood Lords.
 - The `proportion` values should add up to 1.0 (0.69 + 0.13 + 0.16 + 0.02 = 1.0)
 - Each declared unit should be given a priority, where 0 is the highest. This allows resources
to be saved for important units.

## Running the controllers
Let's create a simple bot, demonstrating how to run these controllers.
```python
from ares import AresBot
from ares.behaviors.macro import ProductionController, SpawnController

from sc2.ids.unit_typeid import UnitTypeId as UnitID

class TestBot(AresBot):
    
    @property
    def viking_tank(self) -> dict:
        return {
            UnitID.MARINE: {"proportion": 0.69, "priority": 4},
            UnitID.SIEGETANK: {"proportion": 0.13, "priority": 0},
            UnitID.VIKINGFIGHTER: {"proportion": 0.16, "priority": 3},
            UnitID.RAVEN: {"proportion": 0.02, "priority": 1},
        }

    async def on_step(self, iteration: int) -> None:
        await super(TestBot, self).on_step(iteration)
        
        production_location = self.start_location
        
        # production controller
        self.register_behavior(
            ProductionController(self.viking_tank, production_location)
        )
        
        # spawn controller
        self.register_behavior(
            SpawnController(self.viking_tank)
        )
```

These behaviors can be further customized through arguments, 
please refer to the [API docs](../api_reference/behaviors/macro_behaviors.md)

## Setting up a `MacroPlan`

With a `MacroPlan` you may add several macro behaviors to a single plan, by
defining them in priority order you gain more control over how your macro
tasks are executed versus littering your code with `self.register_behavior(...)`
for several macro behaviors.

Let's enhance our above example, we would like our bot to prioritize building supply.
Followed by workers, maintaining gas structures, spawning units, then lastly adding production:

```python
from ares import AresBot
from ares.behaviors.macro import (
    AutoSupply, 
    BuildWorkers,
    GasBuildingController,
    MacroPlan, 
    ProductionController, 
    SpawnController,
)

from sc2.ids.unit_typeid import UnitTypeId as UnitID

class TestBot(AresBot):
    
    @property
    def viking_tank(self) -> dict:
        return {
            UnitID.MARINE: {"proportion": 0.69, "priority": 4},
            UnitID.SIEGETANK: {"proportion": 0.13, "priority": 0},
            UnitID.VIKINGFIGHTER: {"proportion": 0.16, "priority": 3},
            UnitID.RAVEN: {"proportion": 0.02, "priority": 1},
        }

    async def on_step(self, iteration: int) -> None:
        await super(TestBot, self).on_step(iteration)
        
        production_location = self.start_location
        
        macro_plan: MacroPlan = MacroPlan()
        macro_plan.add(AutoSupply(production_location))
        macro_plan.add(BuildWorkers(to_count=48))
        macro_plan.add(GasBuildingController(to_count=8))
        macro_plan.add(SpawnController(self.viking_tank))
        macro_plan.add(ProductionController(
            self.viking_tank, production_location
        ))
        
        # only need to register once for whole plan
        self.register_behavior(macro_plan)
```


