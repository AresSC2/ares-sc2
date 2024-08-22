## Selecting a worker
If you're using the [Mining behavior](../api_reference/behaviors/macro_behaviors.md#ares.behaviors.macro.mining.Mining) 
and need to select workers
to perform tasks, then you should request `ares` to release workers from mining.

#### Problem

Behind the scenes, Ares designates workers to `UnitRole.GATHERING` and automatically assigns 
specific resources to each worker. If you try to steal these workers without informing `ares`
the `Mining` task will send the worker back to mining again.

#### Solution
Opting to 
[select a worker through the mediator](../api_reference/manager_mediator.md#ares.managers.manager_mediator.ManagerMediator.select_worker)
is recommended. 
This not only simplifies internal bookkeeping by removing the worker from mining and assigned resource
but also prioritizes a worker 
that isn't currently involved in mining or holding resources. The selection process even extends to workers at 
distant mineral patches whenever possible. 
Additionally, it's worth considering assigning a fresh role to the worker to preempt potential 
reassignment by the Mining task. Here's an example:<br/>
```python
from ares.consts import UnitRole

if worker := self.mediator.select_worker(
        target_position=self.start_location
    ):
    self.mediator.assign_role(tag=worker.tag, role=UnitRole.DEFENDING)
```
And to retrieve workers with a `DEFENDING` role: <br/>
```python
from sc2.ids.unit_typeid import UnitTypeId
from sc2.units import Units

defending_workers: Units = self.mediator.get_units_from_role(
    role=UnitRole.DEFENDING, unit_type=UnitTypeId.SCV
)
```

## Mixing `python-sc2` and `ares-sc2`

If starting with a blank ares bot, all `python-sc2` logic will work as intended.
However, you may start working with `ares` behaviors or methods that may interfere with common `python-sc2`
convenience methods or functions.

### Mining behavior
If you're using the `ares` [Mining behavior](../api_reference/behaviors/macro_behaviors.md#ares.behaviors.macro.mining.Mining),
then this breaks the functionality of the following `python-sc2` convenience methods.

* [`self.build()`](https://github.com/BurnySc2/python-sc2/blob/develop/sc2/bot_ai.py#L894) <br/>
<b>Problem</b> <br/>
Since the `Mining` behavior takes control of all spare workers by default it does not relinquish
control of the worker this method is trying to select. <br/><br/>
<b>Solution</b> <br/>
There are two solutions:<br/>
    * Avoid `python-sc2` methods and use `ares-sc2` build structure functionalities. See: <br/>
    [`BuildStructure`](../api_reference/behaviors/macro_behaviors.md#ares.behaviors.macro.build_structure.BuildStructure) behavior and <br/>
    [`self.mediator.build_with_specific_worker`](../api_reference/manager_mediator.md#ares.managers.manager_mediator.ManagerMediator.build_with_specific_worker) <br/>
    Additionally the build runner uses `ares` build functionality if you're using that.
    * If you want to stay with `python-sc2` for now, the `self.build()` accepts a `build_worker` argument, we can ask `ares` to select a worker and then pass that into the method:
```python
# building_pos is the area you want to build in
building_pos: Point2 = self.start_location

if worker := self.mediator.select_worker(target_position=building_pos):
    # ares has given us a worker, assign it a role so ares doesn't
    # steal it for mining
    self.mediator.assign_role(tag=worker.tag, role=UnitRole.BUILDING)
    # now we are free to use this worker with `self.build())
    await self.build(
        building=UnitTypeId.BARRACKS, 
        near=building_pos, 
        build_worker=worker
    )
    
```

* [`self.expand_now()`](https://github.com/BurnySc2/python-sc2/blob/develop/sc2/bot_ai.py#L216) <br/>
<b>Problem</b> <br/>
Same scenario as `self.build()` but we do not have the same option to pass the worker
into the `expand_now()` as we did with `self.build()`.<br/><br/>
<b>Solution</b> <br/>
However, we can combine `python-sc2` and
`ares-sc2` alternative convenience methods for a similar effect. Example: <br/>
```python
# Use `python-sc2` get_next_expansion to get a new base location
if next_expand_loc := await self.get_next_expansion():
    # ask ares for a worker
    if worker := self.mediator.select_worker(
            target_position=next_expand_loc,
            force_close=True,
    ):
        # use ares build_with_specific_worker worker to build base
        # this will assign worker a new role
        # additionally by using this method, you get some extra functionality!
        # Such as replacing dead building workers and pathing control or worker
        self.mediator.build_with_specific_worker(
            worker=worker,
            structure_type=UnitTypeId.NEXUS,
            pos=next_expand_loc,
        )
```
Note, you could use this solution for other buildings too, if you already calculated
exactly where you will place the structure.

* [`self.distribute_workers()`](https://github.com/BurnySc2/python-sc2/blob/develop/sc2/bot_ai.py#L268) - This
one is obviously broken if you're using `Mining` behavior but added for completion’s sake!

* [`self.select_build_worker()`](https://github.com/BurnySc2/python-sc2/blob/develop/sc2/bot_ai.py#L580) <br/>
<b>Problem</b> <br/>
Similar to previous problems, `python-sc2` will not be able to select a 
worker without `ares-sc2` trying to steal it back. <br/><br/>
<b> Solution</b><br/>
Ask `ares` for a worker <br/>
```python
from ares.consts import UnitRole

if worker := self.mediator.select_worker(
        target_position=self.start_location
    ):
    self.mediator.assign_role(tag=worker.tag, role=UnitRole.BUILDING)
```


### Building structures
This section covers breaking `python-sc2` functionality if you interact with `ares` custom build
tracker in any way. You're maybe using the building tracker if you use the following `ares` features:

* `BuildStructure` macro behavior

* `self.mediator.request_building_placement()`

* Using the `ares` `BuildRunner` system in your bot

#### [`self.already_pending()`](https://github.com/BurnySc2/python-sc2/blob/develop/sc2/bot_ai.py#L838) breaks for pending structures

##### Problem
Due to the custom tracking of workers that are currently on route to construct structures, the
`already_pending()` method in `python-sc2` has no knowledge of these pending structures.

##### Solution
`ares` has an alternative function for pending structures:
```python
# checks workers on route and in progress structures
num_pending_barracks: int = self.structure_pending(UnitTypeId.BARRACKS)
```
You could also check how many workers are on route to build a structure if desired.
For Terran this will return same value as `structure_pending` as worker is always present.
For Protoss or Zerg this will only count workers on route.
```python
# checks workers on route, doesn't include gateways in construction
num_on_route_to_build_gateways: int = self.mediator.get_building_counter[UnitTypeId.GATEWAY]
```


#### Mixing `ares-sc2` and `python-sc2` build methods
There are no known breakages here, but a word of warning that mixing building structures via
`ares` building methods and `python-sc2` find placement queries could have
unintended consequences.
If possible try to stick with one system or the other, or limit mixing.
`ares` in the background will check if position is available before building so mixing may
be fine in most cases.

Example `ares-sc2` functions and methods that may interfere with `python-sc2` convenience methods:<br/>

  * `BuildStructure` behavior <br/>
  * `self.mediator.request_building_placement()`<br/>
  * Using `ares` `BuildRunner` system in your bot<br/>

These could interfere with following `python-sc2` methods:<br/>

  * `self.build()`<br/>
  * `self.find_placement()`<br/>
  * Your own calculated placements

## Selecting a unit already assigned to a `UnitSquad`
If you are using `ares-sc2` [unit squad system](../api_reference/manager_mediator.md#ares.managers.manager_mediator.ManagerMediator.get_squads),
and you want to select a unit already assigned to a squad then you should take care to remove the unit to ensure
accurate squad calculations. You can do so by making the following mediator request:

```python
from sc2.unit import Unit

# pretend this unit is already assigned to a unit squad
unit: Unit = self.units[0]
self.mediator.remove_tag_from_squads(tag=unit.tag)

```

Note if you're using the `ares` role system, when assigning a unit a new role,
units are removed from squads automatically. So this should work too:
```python
from ares.consts import UnitRole
from sc2.unit import Unit

# pretend this unit is already assigned to a unit squad
unit: Unit = self.units[0]
# switches unit to new role, and removes from any squad
self.mediator.assign_role(tag=unit.tag, role=UnitRole.DEFENDING)

```

## Other gotchas?
Found something not listed here? Please feel free to contribute to the docs or raise an issue
in the `ares-sc2` github repo.

