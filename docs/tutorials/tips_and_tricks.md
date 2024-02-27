# Helpful Hints and Pointers

## Selecting a worker 
This aspect becomes especially meaningful, particularly in the context of using the 
[`Mining` `MacroBehavior`](../api_reference/behaviors/macro_behaviors.md#ares.behaviors.macro.mining.Mining). 
Behind the scenes, Ares designates workers to the `UnitRole.GATHERING` and automatically assigns 
specific resources to each worker. Therefore, opting to 
[select a worker through the mediator](../api_reference/manager_mediator.md#ares.managers.manager_mediator.ManagerMediator.select_worker)
is recommended. 
This not only simplifies internal bookkeeping by removing the worker but also prioritizes a worker 
that isn't currently involved in mining or holding resources. The selection process even extends to workers at 
distant mineral patches whenever possible. 
Additionally, it's worth considering assigning a fresh role to the worker to preempt potential 
reassignment by the Mining task. Here's an example:

```python
from ares.consts import UnitRole

if worker := self.mediator.select_worker(
        target_position=self.start_location
    ):
    self.mediator.assign_role(tag=worker.tag, role=UnitRole.DEFENDING)
```

And to retrieve workers with a `DEFENDING` role:
```python
from sc2.ids.unit_typeid import UnitTypeId
from sc2.units import Units

defending_workers: Units = self.mediator.get_units_from_role(
    role=UnitRole.DEFENDING, unit_type=UnitTypeId.SCV
)
```

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
