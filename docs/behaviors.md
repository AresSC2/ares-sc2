WARNING! Behaviors implementation is in early stage of development, and there
will likely be breaking changes in the future

# Typical Usage
```py
from ares import AresBot
from ares.behaviors.mining import Mining

class MyBot(AresBot):
    async def on_step(self, iteration: int) -> None:
        await super(MyBot, self).on_step(iteration)
        self.register_behavior(Mining())
```

Typical behavior usage

::: ares.behaviors.mining
    options:
        show_root_heading: true