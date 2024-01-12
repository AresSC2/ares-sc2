When it comes to elevating your bot's strategic capabilities, leveraging the unit role management 
system in `ares-sc2` becomes an invaluable asset.

<b>Let's consider a simple yet effective example: orchestrating ling harassment.</b>

<b>The Scenario:</b> Picture an early-game offensive with 2 roaches and 12 zerglings. 
However, the enemy has left their third base unguarded. 
What if, amidst the distraction caused by our main force, we could dispatch 
half of our zerglings to assail the vulnerable third base?

## Basic A-Move
Initially, let's implement a straightforward a-move bot using only `python-sc2`, devoid of any `ares-sc2` logic.


```python
from ares import AresBot

from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from sc2.units import Units

class MyBot(AresBot):
    LING_ROACH_TYPES: set[UnitTypeId] = {
        UnitTypeId.ZERGLING, UnitTypeId.ROACH
    }
    
    def __init__(self, game_step_override=None):
        """Initiate custom bot"""
        super().__init__(game_step_override)
        

    async def on_step(self, iteration: int) -> None:
        await super(MyBot, self).on_step(iteration)

        if ling_roach_force := self.units(self.LING_ROACH_TYPES):
            attack_target = self.enemy_start_locations[0]
            self._micro_ling_and_roaches(
                ling_roach_force, attack_target
            )
            
            
    def _micro_ling_and_roaches(
        self, ling_roach_force: Units, target: Point2
    ) -> None:
        for unit in ling_roach_force:
            unit.attack(target)

```

This basic strategy involves a simple attack-move command, lacking any intricate logic. 
Now, let's introduce unit roles and assign them dynamically using the `on_unit_created` hook.

```python
from ares import AresBot

# ADD IMPORT
from ares.consts import UnitRole

from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from sc2.units import Units
from sc2.unit import Unit

class MyBot(AresBot):
    LING_ROACH_TYPES: set[UnitTypeId] = {
        UnitTypeId.ZERGLING, UnitTypeId.ROACH
    }
    
    def __init__(self, game_step_override=None):
        """Initiate custom bot"""
        super().__init__(game_step_override)
        

    async def on_step(self, iteration: int) -> None:
        await super(MyBot, self).on_step(iteration)
        
        ling_roach_force: Units = self.mediator.get_units_from_role(
            role=UnitRole.ATTACKING
        )
        if ling_roach_force:
            attack_target = self.enemy_start_locations[0]
            self._micro_ling_and_roaches(
                ling_roach_force, attack_target
            )
            
    async def on_unit_created(self, unit: Unit) -> None:
        await super(MyBot, self).on_unit_created(unit)

        # assign all units to ATTACKING role by default
        if unit.type_id in self.LING_ROACH_TYPES:
            self.mediator.assign_role(
                tag=unit.tag, role=UnitRole.ATTACKING
            )
            
            
    def _micro_ling_and_roaches(
        self, ling_roach_force: Units, target: Point2
    ) -> None:
        for unit in ling_roach_force:
            unit.attack(target)

```


This enhancement allows us to categorize units into roles upon creation, 
enabling us to later retrieve our attacking force using:

```python
ling_roach_force: Units = self.mediator.get_units_from_role(
    role=UnitRole.ATTACKING
)
```

## Implementing Ling Harassment

Now, let's add a layer of complexity by selectively assigning half of the zerglings to a harassment role.

```python
from ares import AresBot

from ares.consts import UnitRole

from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from sc2.units import Units
from sc2.unit import Unit

class MyBot(AresBot):
    LING_ROACH_TYPES: set[UnitTypeId] = {
        UnitTypeId.ZERGLING, UnitTypeId.ROACH
    }
    
    def __init__(self, game_step_override=None):
        """Initiate custom bot"""
        super().__init__(game_step_override)
        
        # Add attribute to remember assigning ling harass
        self._assigned_ling_harass: bool = False
        

    async def on_step(self, iteration: int) -> None:
        await super(MyBot, self).on_step(iteration)
        
        # we can now retrieve our units based on roles
        ling_roach_force: Units = self.mediator.get_units_from_role(
            role=UnitRole.ATTACKING
        )
        ling_harassers: Units = self.mediator.get_units_from_role(
            role=UnitRole.HARASSING
        )
        
        if ling_roach_force:
            if not self._assigned_ling_harass:
                self._assign_ling_harass(ling_roach_force)
                self._assigned_ling_harass = True
                
            attack_target = self.enemy_start_locations[0]
            self._micro_ling_and_roaches(
                ling_roach_force, attack_target
            )
            
        if ling_harassers:
            self._micro_ling_harassers(ling_harassers)
            
    async def on_unit_created(self, unit: Unit) -> None:
        await super(MyBot, self).on_unit_created(unit)

        # assign all units to ATTACKING role by default
        if unit.type_id in self.LING_ROACH_TYPES:
            self.mediator.assign_role(tag=unit.tag, role=UnitRole.ATTACKING)
            
    def _assign_ling_harass(self, ling_roach_force: Units) -> None:
        # get all lings from our force
        lings: list[Unit] = [
            u for u in ling_roach_force if u.type_id == UnitTypeId.ZERGLING
        ]
        
        # iterate through lings
        for i, ling in enumerate(lings):
            # if current iteration is an even number, assign ling to harass
            # this should select half lings
            if i % 2 == 0:
                # actually assign the role
                self.mediator.assign_role(
                    tag=ling.tag, role=UnitRole.HARASSING
                )
    
    def _micro_ling_and_roaches(
        self, ling_roach_force: Units, target: Point2
    ) -> None:
        # Here we micro the main force
        for unit in ling_roach_force:
            unit.attack(target)
            
    def _micro_ling_harassers(self, ling_harassers: Units) -> None:
        # Here we micro the harass force
        for unit in ling_harassers:
            # now do whatever you want with these harassing units!
            # here we ask ares for a potential enemy third location
            unit.attack(self.mediator.get_enemy_third)

```

In this improved version, we assign ling harassment 
role to every second zergling in our attacking force. We can then retrieve units
based on their role and micro them accordingly.

Please note this is an 
example that assumes 12 zerglings already exist. In your own bot, the logic
should flow accordingly for your scenario, like ensuring you already have army units! 
Also, you may want to dynamically
assign harass throughout the game based on intel rather than as a one-off task.

## Unit Role tips and tricks
### Switching roles
For example, switching units from `ATTACKING` to `DEFENDING`

```python
self.mediator.switch_roles(
    from_role=UnitRole.ATTACKING, to_role=UnitRole.DEFENDING
)
```

### Selecting unit types from role
For example, you have many harasser unit types assigned such as banshee, hellions and reapers, but you only
want the banshees:

```python
self.mediator.get_units_from_role(
    role=UnitRole.HARASSING, unit_type={UnitTypeId.BANSHEE}
)
```

### Getting units from multiple roles
```python
self.mediator.get_units_from_roles(
    roles={UnitRole.HARASSING, UnitRole.DROP_UNITS_ATTACKING}
)
```

### Clear a role
Removes a unit from the unit role system completely.
```python
self.mediator.clear_role(tag=unit.tag)
```

### Ares's role dictionary
Might be useful for debugging
```python
self.mediator.get_unit_role_dict
```

