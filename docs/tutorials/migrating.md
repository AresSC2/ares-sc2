Migrating from an existing bot made with burny's [python-sc2](https://github.com/BurnySc2/python-sc2) should
be simple in most cases.

# Installing `ares-sc2`
## Using the starter bot template
This will likely be simplest if you're willing to follow the starter bot structure and conventions. Not only that,
if you make a new github repository based on this template, you'll benefit from automated ladder ready
zip builds via github actions on each push to the `main` branch.

1. Follow the guide on the [starter-bot-repo](https://github.com/AresSC2/ares-sc2-bot-template), and ensure that
it is running before proceeding.

2. Now let's assume your bot folder has some layout like:
    ```
    MyBot
    └───my_bot
    │   └───some_folder
    │   └───another_folder
    │   └───main.py 
    └───sc2
    └───run.py
    └───ladder.py
    ```

    After setting up the starter-bot repo, the new structure will look like:
    (ignored some files for clarity here)
    ```
    ares-sc2-bot-template
    └───ares-sc2
    └───bot
    │   └───main.py 
    └───scripts
    └───run.py
    └───ladder.py
    ```
    
    You should then replace the contents of the `bot` directory in the starter-bot with the contents of 
    your `my_bot` directory. If your main entry point to your bot is not named `main.py` then ensure
    it is renamed and is placed directly in `bot` diretory, replacing the existing `main.py`. 
    There is no need to move over files or folders like `sc2`, `run.py` or
    `ladder.py` from your existing bot.

3. Go to the `#Converting current `python-sc2` bot to an `ares` bot` section of this guide.

## Installing `ares-sc2` directly
If you want more control then installing from the main [ares-sc2 repo](https://github.com/AresSC2/ares-sc2) might be desired.
Cloning the repo and running `poetry install` should provide everything required to run `ares` with your bot. Please
reach out on the [SC2AI discord server](https://discordapp.com/invite/Emm5Ztz) via the #ares-sc2 channel if you need assistance.

To prepare your bot for ladder release, it is worth familarizing yourself with the `create_ladder_zip.py` script on the [starter bot repo](https://github.com/AresSC2/ares-sc2-bot-template/blob/main/scripts/create_ladder_zip.py). You may need to tweak this based on your own scenario. 

<b>IMPORTANT: You should create your ladder zip on a debian based system running python 3.11.</b> You can use WSL
or docker if on Windows/MAC. We are planning to make this user friendly in the future.

# Converting current `python-sc2` bot to an `ares` bot

Code wise there isn't much to change, `main.py` will need a few changes:

* The main bot object should inherit from `ares-sc2`

    `python-sc2`:
    ```python
    from sc2.bot_ai import BotAI
    
    class MyBot(BotAI):
        pass
    ```
    
    `ares-sc2`:
    ```python
    from ares import AresBot
    
    class MyBot(AresBot):
        pass
    ```
    
* Any `on` `python-sc2` hook methods that you use should add a `super` call

    Only convert the hooks you actually use.

    `python-sc2`:
        ```python
        class MyBot(AresBot):
            async def on_step(self, iteration: int) -> None:
                pass

            async def on_start(self, iteration: int) -> None:
                pass

            async def on_end(self, game_result: Result) -> None:
                pass

            async def on_building_construction_complete(self, unit: Unit) -> None:
                pass

            async def on_unit_created(self, unit: Unit) -> None:
                pass

            async def on_unit_destroyed(self, unit_tag: int) -> None:
                pass

            async def on_unit_took_damage(self, unit: Unit, amount_damage_taken: float) -> None:
                pass
        ```
    
    Replace all `MyBot` with your actual class name

    `ares-sc2`:
        ```python
        class MyBot(AresBot):
            async def on_step(self, iteration: int) -> None:
                await super(MyBot, self).on_step(iteration)
                
                # on_step logic here ...

            async def on_start(self, iteration: int) -> None:
                await super(MyBot, self).on_start(iteration)
                
                # on_start logic here ...

            async def on_end(self, game_result: Result) -> None:
                await super(MyBot, self).on_end(iteration)
                
                # custom on_end logic here ...

            async def on_building_construction_complete(self, unit: Unit) -> None:
                await super(MyBot, self).on_building_construction_complete(iteration)

                # custom on_building_construction_complete logic here ...

            async def on_unit_created(self, unit: Unit) -> None:
                await super(MyBot, self).on_unit_created(unit)

                # custom on_unit_created logic here ...

            async def on_unit_destroyed(self, unit_tag: int) -> None:
                await super(MyBot, self).on_unit_destroyed(unit_tag)

                # custom on_unit_destroyed logic here ...

            async def on_unit_took_damage(self, unit: Unit, amount_damage_taken: float) -> None:
                await super(MyBot, self).on_unit_took_damage(unit, amount_damage_taken)

                # custom on_unit_took_damage logic here ...
        ```
