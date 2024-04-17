<b>Recommended Reading:</b> 
 - Explore how to effectively curate 
[Combat Maneuvers](./combat_maneuver_example.md) with individual units, 
providing insights into the workings of the combat maneuver and behavior system in `ares-sc2`.
 - Previous knowledge of the [unit role system](./assigning_unit_roles.md)  is beneficial

## Why Opt for Unit Squads and Group Behaviors?

 - Enable a squadron of units to function cohesively as a group, rather than as 
individual units lacking consideration for the collective strength in the face of nearby enemies.
 - Gain visibility into the spatial distribution of our units; recognizing scenarios 
where our main squad may have fewer units than smaller squads moving across the map. 
This insight could prompt strategic decisions such as pulling back to allow units to converge.
 - Embrace the concept of group thinking within a squad, unlocking the potential for 
human-like control, where all units respond to a single, coordinated action.

## Group Behavior tutorial

To begin, here's a basic example of a Zerg bot utilizing the unit role system to assign all units to the 
`ATTACKING` role.
```python
from ares import AresBot
from ares.consts import ALL_STRUCTURES, WORKER_TYPES, UnitRole

from sc2.ids.unit_typeid import UnitTypeId
from sc2.unit import Unit
from sc2.units import Units

class ZergBot(AresBot):
    def __init__(self, game_step_override = None):
        super().__init__(game_step_override)
        
    async def on_step(self, iteration: int) -> None:
        # retreive all attacking units
        attackers: Units = self.mediator.get_units_from_role(
            role=UnitRole.ATTACKING
        )

    async def on_unit_created(self, unit: Unit) -> None:
        # When a unit is created, 
        # assign it to ATTACKING using ares unit role system
        await super(ZergBot, self).on_unit_created(unit)
        type_id: UnitTypeId = unit.type_id
        # don't assign structures or workers
        if type_id in ALL_STRUCTURES or type_id in WORKER_TYPES:
            return

        # assign all other units to ATTACKING role by default
        self.mediator.assign_role(tag=unit.tag, role=UnitRole.ATTACKING)
```

Now imagine at some specific moment we would like to separate any roaches into their own
separate hit squad. In an actual game you should choose to do this depending on the 
game state, but for the purposes of clarity in this tutorial lets seperate the roaches
at 6 minutes.

```python
from ares import AresBot
from ares.consts import ALL_STRUCTURES, WORKER_TYPES, UnitRole

from sc2.ids.unit_typeid import UnitTypeId
from sc2.unit import Unit
from sc2.units import Units

class ZergBot(AresBot):
    def __init__(self, game_step_override = None):
        super().__init__(game_step_override)
        
        self._assigned_roach_hit_squad: bool = False
        
    async def on_step(self, iteration: int) -> None:
        await super(ZergBot, self).on_step(iteration)
        # retreive all attacking units
        attackers: Units = self.mediator.get_units_from_role(
            role=UnitRole.ATTACKING
        )
        
        # retreive the roach hit squad, if one has been assigned
        roach_hit_squad: Units = self.mediator.get_units_from_role(
            role=UnitRole.CONTROL_GROUP_ONE, unit_type=UnitTypeId.ROACH
        )
        
        # At 6 minutes assign all roaches to CONTROL_GROUP_ONE
        # This will remove them from ATTACKING automatically
        if not self._assigned_roach_hit_squad and self.time > 360.0:
            self._assigned_roach_hit_squad = True
            roaches: list[Unit] = [
                u for u in attackers if u.type_id == UnitTypeId.ROACH
            ]
            for roach in roaches:
                self.mediator.assign_role(
                    tag=roach.tag, role=UnitRole.CONTROL_GROUP_ONE
                )

    async def on_unit_created(self, unit: Unit) -> None:
        # When a unit is created, 
        # assign it to ATTACKING using ares unit role system
        await super(ZergBot, self).on_unit_created(unit)
        type_id: UnitTypeId = unit.type_id
        # don't assign structures or workers
        if type_id in ALL_STRUCTURES or type_id in WORKER_TYPES:
            return

        # assign all other units to ATTACKING role by default
        self.mediator.assign_role(tag=unit.tag, role=UnitRole.ATTACKING)
```

Notice we have now seperated all roaches from the main `UnitRole.ATTACKING` force and provided them with
a new `UnitRole.CONTROL_GROUP_ONE` role. We can now control these forces separately. Now onto the fun
part of curating group combat maneuvers!

We will add a new method to control our hit squad, let's name it `control_roach_hit_squad()`

```python
from ares import AresBot
from ares.behaviors.combat import CombatManeuver
from ares.behaviors.combat.group import AMoveGroup
from ares.consts import ALL_STRUCTURES, WORKER_TYPES, UnitRole

from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units

class ZergBot(AresBot):
    def __init__(self, game_step_override = None):
        super().__init__(game_step_override)
        
        self._assigned_roach_hit_squad: bool = False
        
    async def on_step(self, iteration: int) -> None:
        await super(ZergBot, self).on_step(iteration)
        # retreive all attacking units
        attackers: Units = self.mediator.get_units_from_role(
            role=UnitRole.ATTACKING
        )
        
        # retreive the roach hit squad, if one has been assigned
        roach_hit_squad: Units = self.mediator.get_units_from_role(
            role=UnitRole.CONTROL_GROUP_ONE, unit_type=UnitTypeId.ROACH
        )
        
        self.control_roach_hit_squad(
            roach_hit_squad=roach_hit_squad, 
            target=self.enemy_start_locations[0]
        )
        
        # At 6 minutes assign all roaches to CONTROL_GROUP_ONE
        # This will remove them from ATTACKING automatically
        if not self._assigned_roach_hit_squad and self.time > 360.0:
            self._assigned_roach_hit_squad = True
            roaches: list[Unit] = [
                u for u in attackers if u.type_id == UnitTypeId.ROACH
            ]
            for roach in roaches:
                self.mediator.assign_role(
                    tag=roach.tag, role=UnitRole.CONTROL_GROUP_ONE
                )
                
    def control_roach_hit_squad(
        self, 
        roach_hit_squad: Units, 
        target: Point2
    ) -> None:
        # declare a new group maneuver
        roach_squad_maneuver: CombatManeuver = CombatManeuver()
        # add group behaviors, these can be behaviors provided by ares
        # or create your own custom group behaviors!
        roach_squad_maneuver.add(
          AMoveGroup(
            group=roach_hit_squad, 
            group_tags={r.tag for r in roach_hit_squad}, 
            target=target
          )
        )
        
        self.register_behavior(roach_squad_maneuver)

    async def on_unit_created(self, unit: Unit) -> None:
        # When a unit is created, 
        # assign it to ATTACKING using ares unit role system
        await super(ZergBot, self).on_unit_created(unit)
        type_id: UnitTypeId = unit.type_id
        # don't assign structures or workers
        if type_id in ALL_STRUCTURES or type_id in WORKER_TYPES:
            return

        # assign all other units to ATTACKING role by default
        self.mediator.assign_role(tag=unit.tag, role=UnitRole.ATTACKING)
```

This method creates a basic "a-move" group maneuver for our roaches. Given a target, the roaches will 
advance towards it. Moreover, `ares-sc2` automatically checks for duplicated actions to prevent action spam, 
enabling your bot to "a-move" akin to a human player.

### Extending the group maneuver
Similar to individual combat maneuvers, Behaviors should be orchestrated in priority order. 
`ares` executes behaviors according to the user-provided order, therefore if a behavior executes and action,
any subsequent behaviors will be ignored. With this in mind, let's add a group behavior 
for when enemies are close. We'd like our roaches to be aggressive, closing in on nearby enemies
using the `StutterGroupForward` behavior. 
Otherwise, if no enemies are present, the `AMoveGroup` behavior will execute:

```python
from cython_extensions import cy_center

from sc2.position import Point2
from sc2.units import Units

from ares.behaviors.combat import CombatManeuver
from ares.behaviors.combat.group import AMoveGroup, StutterGroupForward
from ares.consts import UnitTreeQueryType


def control_roach_hit_squad(
        self, 
        roach_hit_squad: 
        Units, target: Point2
    ) -> None:
    squad_position: Point2 = Point2(cy_center(roach_hit_squad))
    
    # retreive close enemy to the roach squad
    close_ground_enemy: Units = self.mediator.get_units_in_range(
        start_points=[squad_position],
        distances=15.5,
        query_tree=UnitTreeQueryType.EnemyGround,
    )[0]
    
    # declare a new group maneuver
    roach_squad_maneuver: CombatManeuver = CombatManeuver()
    
    # stutter forward to any ground enemies
    # as this behavior is added first to the maneuver it 
    # has the highest priority
    roach_squad_maneuver.add(
      StutterGroupForward(
        group=roach_hit_squad,
        group_tags={u.tag for u in roach_hit_squad},
        group_position=squad_position,
        target=target,
        enemies=close_ground_enemy,
      )
    )
    
    # if StutterGroupForward does not execute, our units will AMove
    roach_squad_maneuver.add(
      AMoveGroup(
        group=roach_hit_squad, 
        group_tags={r.tag for r in roach_hit_squad}, 
        target=target
      )
    )
    
    self.register_behavior(roach_squad_maneuver)
```

## Unit Squads: Enhanced Group Tactics

Our roach_squad_maneuver works well, but controlling roaches as a group has a significant flaw. 
Imagine our roach squad is scattered across the map; issuing StutterGroupForward to roaches 
that don't have nearby enemies is ineffective. Moreover, calculating close enemies to our 
group becomes inaccurate, leading to undesirable behavior.

Thankfully, we can utilize the UnitSquad system in ares-sc2 to split our hit squad into logical groups! 
Let's enhance the control_roach_hit_squad method to incorporate this:

```python
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units

from ares.behaviors.combat import CombatManeuver
from ares.behaviors.combat.group import AMoveGroup, StutterGroupForward
from ares.consts import UnitRole, UnitTreeQueryType
from ares.managers.squad_manager import UnitSquad


def control_roach_hit_squad(
        self, 
        roach_hit_squad: Units, 
        target: Point2
    ) -> None:
    
    squads: list[UnitSquad] = self.mediator.get_squads(
        role=UnitRole.CONTROL_GROUP_ONE, squad_radius=9.0
    )
    for squad in squads:
        squad_position: Point2 = squad.squad_position
        units: list[Unit] = squad.squad_units
        squad_tags: set[int] = squad.tags
        
        # retreive close enemy to the roach squad
        close_ground_enemy: Units = self.mediator.get_units_in_range(
            start_points=[squad_position],
            distances=11.5,
            query_tree=UnitTreeQueryType.EnemyGround,
        )[0]
        
        # declare a new group maneuver
        roach_squad_maneuver: CombatManeuver = CombatManeuver()
        
        # stutter forward to any ground enemies
        # as this behavior is added first to the maneuver it 
        # has the highest priority
        roach_squad_maneuver.add(
          StutterGroupForward(
            group=units,
            group_tags=squad_tags,
            group_position=squad_position,
            target=target,
            enemies=close_ground_enemy,
          )
        )
        
        # if StutterGroupForward does not execute, our units will AMove
        roach_squad_maneuver.add(
          AMoveGroup(
            group=units, 
            group_tags=squad_tags, 
            target=target
          )
        )
        
        self.register_behavior(roach_squad_maneuver)
```

Now, UnitSquad provides attributes such as squad_position, squad_units, and tags, eliminating the 
need for manual calculations. This allows for greater synergy with the group maneuver system, as we
can pass this attributes directly as arguments into group behaviors:

```python
squad: UnitSquad
AMoveGroup(
    group=squad.squad_units, 
    group_tags=squad.tags, 
    target=target
)
```

Our final bot looks a bit like this:

```python
from ares import AresBot
from ares.behaviors.combat import CombatManeuver
from ares.behaviors.combat.group import AMoveGroup, StutterGroupForward
from ares.consts import ALL_STRUCTURES, WORKER_TYPES, UnitRole, UnitTreeQueryType
from ares.managers.squad_manager import UnitSquad

from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units

class ZergBot(AresBot):
    def __init__(self, game_step_override = None):
        super().__init__(game_step_override)
        
        self._assigned_roach_hit_squad: bool = False
        
    async def on_step(self, iteration: int) -> None:
        await super(ZergBot, self).on_step(iteration)
        # retreive all attacking units
        attackers: Units = self.mediator.get_units_from_role(
            role=UnitRole.ATTACKING
        )
        
        # retreive the roach hit squad, if one has been assigned
        roach_hit_squad: Units = self.mediator.get_units_from_role(
            role=UnitRole.CONTROL_GROUP_ONE, unit_type=UnitTypeId.ROACH
        )
        
        self.control_roach_hit_squad(
            roach_hit_squad=roach_hit_squad, 
            target=self.enemy_start_locations[0]
        )
        
        # At 6 minutes assign all roaches to CONTROL_GROUP_ONE
        # This will remove them from ATTACKING automatically
        if not self._assigned_roach_hit_squad and self.time > 360.0:
            self._assigned_roach_hit_squad = True
            roaches: list[Unit] = [
                u for u in attackers if u.type_id == UnitTypeId.ROACH
            ]
            for roach in roaches:
                self.mediator.assign_role(
                    tag=roach.tag, role=UnitRole.CONTROL_GROUP_ONE
                )
                
    def control_roach_hit_squad(
            self, 
            roach_hit_squad: Units, 
            target: Point2
        ) -> None:
        
        squads: list[UnitSquad] = self.mediator.get_squads(
            role=UnitRole.CONTROL_GROUP_ONE, squad_radius=9.0
        )
        for squad in squads:
            squad_position: Point2 = squad.squad_position
            units: list[Unit] = squad.squad_units
            squad_tags: set[int] = squad.tags
            
            # retreive close enemy to the roach squad
            close_ground_enemy: Units = self.mediator.get_units_in_range(
                start_points=[squad_position],
                distances=11.5,
                query_tree=UnitTreeQueryType.EnemyGround,
            )[0]
            
            # declare a new group maneuver
            roach_squad_maneuver: CombatManeuver = CombatManeuver()
            
            # stutter forward to any ground enemies
            # as this behavior is added first to the maneuver it 
            # has the highest priority
            roach_squad_maneuver.add(
              StutterGroupForward(
                group=units,
                group_tags=squad_tags,
                group_position=squad_position,
                target=target,
                enemies=close_ground_enemy,
              )
            )
            
            # if StutterGroupForward does not execute, our units will AMove
            roach_squad_maneuver.add(
              AMoveGroup(
                group=units, 
                group_tags=squad_tags, 
                target=target
              )
            )
            
            self.register_behavior(roach_squad_maneuver)

    async def on_unit_created(self, unit: Unit) -> None:
        # When a unit is created, 
        # assign it to ATTACKING using ares unit role system
        await super(ZergBot, self).on_unit_created(unit)
        type_id: UnitTypeId = unit.type_id
        # don't assign structures or workers
        if type_id in ALL_STRUCTURES or type_id in WORKER_TYPES:
            return

        # assign all other units to ATTACKING role by default
        self.mediator.assign_role(tag=unit.tag, role=UnitRole.ATTACKING)
```
