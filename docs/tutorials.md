# Tutorials

## Build Runner System
The Build Runner System is a tool that enables swift build prototyping through a configuration file. 
Optional data usage can be incorporated to maintain build history.

### Declaring openings
To initiate the Build Runner, a `<my_race_lowercase>_builds.yml` file should be included in the root directory of your bot project. 
If you are playing as the Random race, then a yml file must be declared for each race that you wish ares to handle 
openings and/or data management for.

Below is an example of a valid yml file. (`protoss_builds.yml`)
```yml
# Save the game opening and result to disk?
# Setting to `True` allows Ares to select a new opening after defeat
UseData: True
# How should we choose a build? Cycle is the only option for now
BuildSelection: Cycle
# For each Race / Opponent ID choose a build selection
BuildChoices:
    # test_123 is active if Debug: True (set via a `config.yml` file)
    test_123:
        BotName: Test
        Cycle:
            - FastExpand
            
    Protoss:
        BotName: ProtossRace
        Cycle:
            - FastExpand
            - WorkerBuild
            
    Random:
        BotName: RandomRace
        Cycle:
            - FastExpand
            
    Terran:
        BotName: TerranRace
        Cycle:
            - FastExpand
            
    Zerg:
        BotName: ZergRace
        Cycle:
            - FastExpand
            - WorkerBuild
    
    # Can also use specific opponent ids (overrides race options above)
    a_bot_opponent_id_from_aiarena:
        BotName: QueenBot
        Cycle:
            - FastExpand

Builds:
    WorkerBuild:
        ConstantWorkerProduction: True
        OpeningBuildOrder:
            - 12 chrono @ nexus
            - 14 pylon @ ramp
            - 16 gateway
    FastExpand:
        ConstantWorkerProduction: False
        OpeningBuildOrder:
            ['12 worker', '13 worker', '14 supply', '14 worker', '14 chrono @ nexus',
             '15 worker', '15 gateway', '16 worker', '17 expand', '17 worker', '17 zealot']

```

Note the two different ways of declaring builds. Turning `ConstantWorkerProduction` on allows a readable
build order but may be undesirable in a fine-tuned build. 
Each build order statement should begin with a supply count, the step will not commence till
the supply is equal or greater than this supply. Therefore, if this is not important, or you're not sure put a low value.
ie. `["14 pylon", "1 gateway"]` will work just as well.


Under the BuildChoices key, you should include keys for each enemy race. You may also use opponent IDs instead of races 
to select specific openings for opponents. Under the Cycle key, declare the opening build names for that opponent or 
race. For each build name, ensure that there is a corresponding build name under Builds.

### Valid build order options
Each item in the build order should contain a string, with the first word being the command. 
This supports any UnitTypeID type from python-sc2, which can be found [here.](https://github.com/BurnySc2/python-sc2/blob/develop/sc2/ids/unit_typeid.py)


A few extra options are also supported:
```python
class BuildOrderOptions(str, Enum):
    CHRONO = "CHRONO"
    GAS = "GAS"
    EXPAND = "EXPAND"
    SUPPLY = "SUPPLY"
    WORKER = "WORKER"
```

Additionally, strings may contain targets such as '14 pylon @ ramp', where the third word should contain the target 
command. The following targets are currently supported:
```python
class BuildOrderTargetOptions(str, Enum):
    RAMP = "RAMP"
```

If you are using chrono, then the target should contain the structure ID that represents a `UnitTypeID` type, 
for example:

`chrono @ gateway`


### Build complete
Upon completion of the build, a typical bot workflow should allow for dynamic production. To check whether the opening 
has been completed or not, you can use the following method call:

```self.build_order_runner.opening_completed```

This will return a boolean value indicating whether the opening has been completed or not.

### Get the opening build name
Retrieve the opening build name using the following method call:

```self.build_order_runner.chosen_opening```

This method will return a string value containing the name of the currently selected build from the 
`<my_race_lowercase>_builds.yml` file.


