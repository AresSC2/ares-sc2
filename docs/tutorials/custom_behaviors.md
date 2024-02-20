<b>Recommended reading:</b> How to curate [Combat Maneuver's](./combat_maneuver_example.md) using
existing `Behavior`'s in `ares-sc2`.
Before curating custom behaviors, take a look at some of the 
core [behaviors in ares-sc2](https://github.com/AresSC2/ares-sc2/tree/main/src/ares/behaviors), to get an idea
how one should be structured.

Let's start with a simple example, we have a group of marines and tanks we would like to micro.
Let's use the `CombatManeuver` functionality in `ares-sc2` to orchestrate a simple a-move across the
map.

```python
from ares import AresBot
from ares.behaviors.combat import CombatManeuver
from ares.behaviors.combat.individual import AMove

from sc2.ids.unit_typeid import UnitTypeId
from sc2.units import Units
from sc2.position import Point2


class MyBot(AresBot):
    MARINE_TANK_TYPES: set[UnitTypeId] = {
        UnitTypeId.MARINE, UnitTypeId.SIEGETANKSIEGED, UnitTypeId.SIEGETANK
    }

    def __init__(self, game_step_override=None):
        """Initiate custom bot"""
        super().__init__(game_step_override)

    async def on_step(self, iteration: int) -> None:
        await super(MyBot, self).on_step(iteration)

        if marine_tank_force := self.units(self.MARINE_TANK_TYPES):
            attack_target = self.enemy_start_locations[0]
            self._micro_marine_tank(marine_tank_force, attack_target)

    def _micro_marine_tank(self, units: Units, target: Point2) -> None:
        for unit in units:
            # set up a new CombatManeuver for this unit
            offensive_attack: CombatManeuver = CombatManeuver()
            # add AMove to this maneuver
            offensive_attack.add(AMove(unit, target))
            # register the maneuver so it gets executed
            self.register_behavior(offensive_attack)
```

This is all working great, how about now we add decision-making to siege or unsiege our tanks?

The problem: there isn't an existing combat behavior in `ares-sc2` to do this. This is partly intentional
since sieging/unsieging tanks is a strategic decision personal to your bot.

We propose a solution: create a reusable custom combat behavior that `ares-sc2` understands and can be executed.

As long as our behavior class follows the `CombatIndividualBehavior` Protocol, we can add it to
our existing `offensive_attack` `CombatManeuver`. 
- `CombatIndividualBehavior` Protocol says we should implement an `execute` method with the following signature:

`def execute(self, ai: "AresBot", config: dict, mediator: ManagerMediator) -> bool:`

Notice this method should return a `booleon`, this should return `True` if this implemented
`CombatIndividualBehavior` carried out an action, and `False` otherwise.

With this is mind let's implement a `SiegeTankDecision` custom behavior, you could save this in a new
`siege_tank_decision.py` file:

```python
# siege_tank_decision.py`
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ares.behaviors.combat.individual import CombatIndividualBehavior
from ares.cython_extensions.geometry import cy_distance_to
from ares.managers.manager_mediator import ManagerMediator
from ares.consts import UnitTreeQueryType
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId as UnitID
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units

if TYPE_CHECKING:
    from ares import AresBot

@dataclass
class SiegeTankDecision(CombatIndividualBehavior):
    """Decide if a tank should either siege or unsiege.

    Attributes
    ----------
    unit : Unit
        The siege tank unit.
    """

    unit: Unit

    def execute(self, ai: "AresBot", config: dict, mediator: ManagerMediator) -> bool:
        unit_pos: Point2 = self.unit.position
        type_id: UnitID = self.unit.type_id
        
        # get near enemy ground
        # ares uses `KDTree` algorithm for faster distance queries
        # let's make use of that
        near_enemy_ground: Units = mediator.get_units_in_range(
            start_points=[self.unit.position],
            distances=14,
            query_tree=UnitTreeQueryType.EnemyGround,
        )[0]

        if type_id == UnitID.SIEGETANK:
            # if enemies are not too close, and enough ground enemy around then siege
            close_to_tank: list[Unit] = [
                e for e in near_enemy_ground if cy_distance_to(e.position, unit_pos) < 6.5
            ]
            if len(close_to_tank) == 0 and (
                (ai.get_total_supply(near_enemy_ground) >= 4.0 and len(near_enemy_ground) > 3)
            ):
                self.unit(AbilityId.SIEGEMODE_SIEGEMODE)
                return True

        elif type_id == UnitID.SIEGETANKSIEGED:
            # just a general if nothing around then unsiege
            if len(near_enemy_ground) == 0:
                self.unit(AbilityId.UNSIEGE_UNSIEGE)
                return True
        
        # no action was carried out
        return False
```

This is an example, this could be tweaked and extended as required. Meanwhile, this custom `Behavior`
can be reused in other scenarios!

Let's update our original code to import this `Behavior` and include it in our `offensive_attack` maneuver:

```python
from ares import AresBot
from ares.behaviors.combat import CombatManeuver
from ares.behaviors.combat.individual import AMove

from sc2.ids.unit_typeid import UnitTypeId
from sc2.units import Units
from sc2.position import Point2

# IMPORT SiegeTankDecision, modify import based on where you saved it
from bot.siege_tank_decision import SiegeTankDecision


class MyBot(AresBot):
    MARINE_TANK_TYPES: set[UnitTypeId] = {
        UnitTypeId.MARINE, UnitTypeId.SIEGETANKSIEGED, UnitTypeId.SIEGETANK
    }

    def __init__(self, game_step_override=None):
        """Initiate custom bot"""
        super().__init__(game_step_override)

    async def on_step(self, iteration: int) -> None:
        await super(MyBot, self).on_step(iteration)

        if marine_tank_force := self.units(self.MARINE_TANK_TYPES):
            attack_target = self.enemy_start_locations[0]
            self._micro_marine_tank(marine_tank_force, attack_target)

    def _micro_marine_tank(self, units: Units, target: Point2) -> None:
        for unit in units:
            # set up a new CombatManeuver for this unit
            offensive_attack: CombatManeuver = CombatManeuver()
            
            # ADD OUR CUSTOM SIEGE BEHAVIOR HERE
            # Maneuvers should be set up so that higher priority tasks are added first.
            # If this returns False for a tank, then the 
            # AMove behavior will try to execute an action instead
            offensive_attack.add(SiegeTankDecision(unit))
            
            # add AMove to this maneuver
            # AMove always returns True so should typically be added at the end
            offensive_attack.add(AMove(unit, target))
            # register the maneuver so it gets executed
            self.register_behavior(offensive_attack)
```


