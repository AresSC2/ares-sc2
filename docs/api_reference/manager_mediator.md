To enable communication between managers in ares-sc2, the mediator pattern is used internally. If you need to request 
information or perform an action from a manager, it is strongly recommended that you do so through the mediator, 
which can be accessed via `self.mediator`. For example:

```python
ground_grid: np.ndarray = self.mediator.get_ground_grid
```

::: ares.managers.manager_mediator.ManagerMediator
    options:
        show_bases : false
