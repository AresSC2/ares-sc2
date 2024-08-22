The ares framework comes with the [SC2MapAnalysis library](https://github.com/spudde123/SC2MapAnalysis) already integrated. This integration 
provides access to the library's grid and pathing features, enabling ares to offer a variety of 
preconfigured grids and pathing functions right out of the box. This also enables users to create
their own custom grids which they can use with existing ares pathing and behavior methods.

## What is a grid?
A grid is essentially a two-dimensional array, where each element represents an x,y coordinate in the game, 
and the value of that element will contain some numerical value.
A basic ground grid might contain zeroes for unpathable tiles and ones for pathable. See a visual example
below of a simple pathing ground grid the Blizzard API provides.

![basic_grid](https://github.com/user-attachments/assets/cea0da41-0c60-47b5-883b-7ab28f34ce81)

A basic grid can be used for all kinds of purposes, but in the context of combat we would like
to add cost (sometimes known as influence) to this map. For example in pathable cells that
contain enemy dangers we might increase the value from the default of `1.0` to some value that
represents the danger level. With this information we can enhance our micro opportunities, and
any pathing queries in `ares` (via the SC2MapAnalysis library) will take into account cost
when calculating paths.

## Existing grids in ares
`ares` has several grids with relevant enemy cost added, they are opinionated but are intended
to help a user quickly get up and running with pathfinding and enemy influence. At the end of this tutorial
we describe how to create your own grids.

### Grids
The following grids are already setup ready to use out of the box.

- [`self.mediator.get_air_avoidance_grid`](../api_reference/manager_mediator.md#ares.managers.manager_mediator.ManagerMediator.get_air_avoidance_grid) an air
grid containing dangerous effects to avoid. For example storms, ravager biles, parasitic bombs, nukes etc.
- [`self.mediator.get_air_grid`](../api_reference/manager_mediator.md#ares.managers.manager_mediator.ManagerMediator.get_air_grid) an air
grid containing all enemy units and effects dangerous to air.
- [`self.mediator.get_air_vs_ground_grid`](../api_reference/manager_mediator.md#ares.managers.manager_mediator.ManagerMediator.get_air_vs_ground_grid) a specialised
air grid where ground pathable tiles have increased cost. The idea behind this one is for air units will favour high ground areas when 
using pathing queries.
- [`self.mediator.get_climber_grid`](../api_reference/manager_mediator.md#ares.managers.manager_mediator.ManagerMediator.get_climber_grid) - Same
as `get_ground_grid` but areas where reapers can jump, or colossus can climb are pathable.
- [`self.mediator.get_ground_grid`](../api_reference/manager_mediator.md#ares.managers.manager_mediator.ManagerMediator.get_ground_grid) - A
ground grid that contains all enemy units and effects dangerous to ground.
- [`self.mediator.get_ground_to_air_grid `](../api_reference/manager_mediator.md#ares.managers.manager_mediator.ManagerMediator.get_ground_to_air_grid) - A
air grid that contains only cost from ground enemies that are dangerous to air.

## Example grid usage
This section contains practical uses for influence and pathing.

### Pathing
`ares` contains several ways to use pathing:

- [`self.mediator.find_path_next_point`](../api_reference/manager_mediator.md#ares.managers.manager_mediator.ManagerMediator.find_path_next_point)<br/>
Where you have a unit, but you just need the next point to move along a path.
```python
move_to: Point2 = self.mediator.find_path_next_point(
    start=self.start_location,
    target=self.enemy_start_locations[0],
    grid=self.mediator.get_air_grid
)
```

- [`self.mediator.find_raw_path`](../api_reference/manager_mediator.md#ares.managers.manager_mediator.ManagerMediator.find_raw_path)<br/>
Get the entire queried path.
```python
path: list[Point2] = self.mediator.find_raw_path(
    start=self.start_location,
    target=self.enemy_start_locations[0],
    grid=self.mediator.get_air_grid
)
```

- [`self.mediator.find_low_priority_path`](../api_reference/manager_mediator.md#ares.managers.manager_mediator.ManagerMediator.find_low_priority_path)<br/>
This will calculate an entire path but then only return several points along this path. <br/>
Useful for queuing up commands, for example an overlord going to a spotting position.
```python
path: list[Point2] = self.mediator.find_low_priority_path(
    start=self.start_location,
    target=self.enemy_start_locations[0],
    grid=self.mediator.get_air_grid
)
```

- [`PathUnitToTarget`](../api_reference/behaviors/combat_behaviors.md#ares.behaviors.combat.individual.path_unit_to_target.PathUnitToTarget)<br/>
A `CombatBehavior` that takes care of pathing and moving the unit.
```python
from ares.behaviors.combat.individual import PathUnitToTarget
from ares.behaviors.behavior import Behavior

unit: Unit = self.workers[0]


path_unit: Behavior = PathUnitToTarget(
    unit=unit,
    grid=self.mediator.get_ground_grid,
    target=self.game_info.map_center
)
self.register_behavior(path_unit)
```

- [`PathGroupToTarget`](../api_reference/behaviors/combat_behaviors.md#ares.behaviors.combat.group.path_group_to_target.PathGroupToTarget)<br/>
A `CombatBehavior` that takes care of pathing and moving an entire group.
```python
from ares.behaviors.combat.group import PathGroupToTarget
from ares.behaviors.behavior import Behavior

group: Units = self.workers


path_group: Behavior = PathGroupToTarget(
    start=group.center,
    group=group,
    group_tags={u.tag for u in group},
    grid=self.mediator.get_ground_grid,
    target=self.game_info.map_center
)
self.register_behavior(path_group)
```

### Keeping units safe

- [`self.mediator.find_closest_safe_spot`](../api_reference/manager_mediator.md#ares.managers.manager_mediator.ManagerMediator.find_closest_safe_spot)<br/>
Given a position, find a nearby safe spot. Most useful for working out where to retreat to.
```python
safe_spot: Point2 = self.mediator.find_closest_safe_spot(
    from_pos=self.start_location,
    grid=self.mediator.get_air_avoidance_grid,
    radius=8
)
```

- [`KeepUnitSafe`](../api_reference/behaviors/combat_behaviors.md#ares.behaviors.combat.individual.path_unit_to_target.KeepUnitSafe )<br/>
A `CombatBehavior` that takes care of finding a safe position and moving the unit.
```python
from ares.behaviors.combat.individual import KeepUnitSafe
from ares.behaviors.behavior import Behavior

unit: Unit = self.workers[0]


keep_safe: Behavior = KeepUnitSafe(
    unit=unit,
    grid=self.mediator.get_ground_grid,
)
self.register_behavior(keep_safe)
```

- [`KeepGroupSafe`](../api_reference/behaviors/combat_behaviors.md#ares.behaviors.combat.group.path_group_to_target.KeepGroupSafe)<br/>
A `CombatBehavior` that keeps an entire group safe.
```python
from ares.behaviors.combat.group import KeepGroupSafe 
from ares.behaviors.behavior import Behavior

group: Units = self.workers


keep_group_safe: Behavior = KeepGroupSafe(
    group=group,
    grid=self.mediator.get_ground_grid,
)
self.register_behavior(keep_group_safe)
```

### Checking cost
Grids are `numpy` arrays, and each cell matches the in game position:

```python
import numpy as np
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2

grid: np.ndarray = self.mediator.get_climber_grid

if reapers := self.mediator.get_own_army_dict[UnitTypeId.REAPER]:
    for reaper in reapers:
        pos: Point2 = reaper.position
        reaper_danger_level: float = grid[pos[0], pos[1]]
```

Included with `ares` is the [`cython_extensions-sc2 library`](https://github.com/AresSC2/cython-extensions-sc2), which includes
some helper functions for checking numpy grids.
```python
import numpy as np
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from cython_extensions import cy_point_below_value

grid: np.ndarray = self.mediator.get_climber_grid

if reapers := self.mediator.get_own_army_dict[UnitTypeId.REAPER]:
    for reaper in reapers:
        pos: Point2 = reaper.position
        reaper_is_safe: float = cy_point_below_value(
            grid=grid, 
            position=pos.rounded,
            weight_safety_limit=1.0 # default pathing cell with no danger is 1.0
        )
```

Have a check on the `cython_extensions-sc2` repo docs for other functions including: 

- `cy_all_points_below_max_value`
- `cy_all_points_have_value`
- `cy_last_index_with_value`
- `cy_points_with_value`

## Create your own grids
The available grids in ares are pre-filled with enemy cost based on the developers' perspectives. 
However, you have the flexibility to create your own custom grids. Even better, you can integrate 
these custom grids into existing ares functions and behaviors!

As the [SC2MapAnalysis library](https://github.com/spudde123/SC2MapAnalysis) in integrated into
`ares` let's use that to get a blank grid, then we add cost to the map. See the example below:

```python
from map_analyzer import MapData
from ares import AresBot
import numpy as np
from sc2.position import Point2

class MyBot(AresBot):
    async def on_step(self, iteration: int) -> None:
        # get access to the SC2MapAnalysis library
        map_data: MapData = self.mediator.get_map_data_object
        
        # get a clean ground grid
        my_ground_grid: np.ndarray = map_data.get_pyastar_grid()
        # or an air grid if needed
        my_air_grid: np.ndarray = map_data.get_clean_air_grid()
        
        """
        Add cost to this grid
        For this example, let's make the enemy spawn location
        really dangerous!
        In effect this will draw a circle (20 radius) around the enemy spawn,
        and add 100 cost to all tiles in this circle.
        """
        my_ground_grid = map_data.add_cost(
            position=self.enemy_start_locations[0],
            radius=20,
            grid=my_ground_grid,
            weight=100.5
        )
        
        
        """
        In a real world bot, you probably add cost for enemy units,
        structures and effects, something like:
        """
        radius_buffer: float = 2.0
        for unit in self.all_enemy_units:
            if unit.can_attack_ground:
                my_ground_grid = map_data.add_cost(
                    position=unit.position,
                    radius=unit.ground_range + radius_buffer,
                    grid=my_ground_grid,
                    weight=unit.ground_dps
                )
            if unit.can_attack_air:
                my_air_grid = map_data.add_cost(
                    position=self.enemy_start_locations[0],
                    radius=unit.air_range + radius_buffer,
                    grid=my_air_grid,
                    weight=unit.ground_dps
                )
                
        # now my_ground_grid, my_ground_grid are ready to use
        
        # will find the best path to enemy spawn, factoring in enemy cost
        move_to: Point2 = self.mediator.find_path_next_point(
            start=self.start_location,
            target=self.enemy_start_locations[0],
            grid=my_ground_grid
        )
        
        """
        Use custom grids with any ares method, behavior etc
        """
            



```
