# Helpful Hints and Pointers

## Selecting a worker 
This aspect becomes especially meaningful, particularly in the context of using the 
[`Mining` `MacroBehavior`](/api_reference/behaviors/macro_behaviors.html#ares.behaviors.macro.mining.Mining). 
Behind the scenes, Ares designates workers to the `UnitRole.GATHERING` and automatically assigns 
specific resources to each worker. Therefore, opting to 
[select a worker through the mediator](/api_reference/manager_mediator.html#ares.managers.manager_mediator.ManagerMediator.select_worker)
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
