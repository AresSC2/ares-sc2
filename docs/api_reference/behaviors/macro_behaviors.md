# Typical Usage
```py
from ares import AresBot
from ares.behaviors.macro.mining import Mining

class MyBot(AresBot):
    async def on_step(self, iteration: int) -> None:
        await super(MyBot, self).on_step(iteration)
        self.register_behavior(Mining())
```

::: ares.behaviors.macro.macro_plan
    options:
        show_root_heading: false
        show_root_toc_entry: false 

::: ares.behaviors.macro.addon_swap
    options:
        show_root_heading: false
        show_root_toc_entry: false 

::: ares.behaviors.macro.auto_supply
    options:
        show_root_heading: false
        show_root_toc_entry: false 

::: ares.behaviors.macro.build_structure
    options:
        show_root_heading: false
        show_root_toc_entry: false 

::: ares.behaviors.macro.build_workers
    options:
        show_root_heading: false
        show_root_toc_entry: false

::: ares.behaviors.macro.expansion_controller
    options:
        show_root_heading: false
        show_root_toc_entry: false

::: ares.behaviors.macro.gas_building_controller
    options:
        show_root_heading: false
        show_root_toc_entry: false

::: ares.behaviors.macro.mining
    options:
        show_root_heading: false
        show_root_toc_entry: false 

::: ares.behaviors.macro.production_controller
    options:
        show_root_heading: false
        show_root_toc_entry: false 

::: ares.behaviors.macro.restore_power
    options:
        show_root_heading: false
        show_root_toc_entry: false 

::: ares.behaviors.macro.spawn_controller
    options:
        show_root_heading: false
        show_root_toc_entry: false

::: ares.behaviors.macro.tech_up
    options:
        show_root_heading: false
        show_root_toc_entry: false 

::: ares.behaviors.macro.upgrade_controller
    options:
        show_root_heading: false
        show_root_toc_entry: false
