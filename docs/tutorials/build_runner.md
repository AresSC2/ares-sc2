
## Build Runner System
The Build Runner System is a tool that enables swift build prototyping through a configuration file. 
Optional data usage can be incorporated to maintain build history. IMPORTANT: The build runner system
is designed only for curating optimized build orders in the first few minutes of the game. Your bot 
should switch to dynamic behavior after completion, checked via ```self.build_order_runner.opening_completed```.

### Declaring openings
To initiate the Build Runner, a `<my_race_lowercase>_builds.yml` file should be included in the root directory of 
your bot project. [Check starter-bot for example](https://github.com/AresSC2/ares-sc2-starter-bot)
If you are playing as the Random race, then a yml file must be declared for each race that you wish ares to handle 
openings and/or data management for.

Below is an example of a valid yml file. (`protoss_builds.yml`)
```yaml
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
        ConstantWorkerProductionTill: 22
        OpeningBuildOrder:
            - 12 chrono @ nexus
            - 14 pylon @ ramp
            - 16 gateway
    FastExpand:
        ConstantWorkerProductionTill: 0
        OpeningBuildOrder:
            ['12 worker', '13 worker', '14 supply', '14 worker', '14 chrono @ nexus',
             '15 worker', '15 gateway', '16 worker', '17 expand', '17 worker', '17 zealot']

```

Note the two different ways of declaring builds. Turning `ConstantWorkerProductionTill` on allows a readable
build order but may be undesirable in a fine-tuned build. (setting to 0 disables)
Each build order statement should begin with a supply count, the step will not commence till
the supply is equal or greater than this supply. Therefore, if this is not important, or you're not sure put a low value.
ie. `["14 pylon", "1 gateway"]` will work just as well.


Under the BuildChoices key, you should include keys for each enemy race. You may also use opponent IDs instead of races 
to select specific openings for opponents. Under the Cycle key, declare the opening build names for that opponent or 
race. For each build name, ensure that there is a corresponding build name under Builds.

<b>WARNING</b>: The build runner is dumb by nature, and expected to be told exactly what to do. Please
be careful adding build steps that are impossible to commence. Such as adding a barracks before a 
supply depot or a gateway before pylon.

### Valid build order options
Each item in the build order should contain a string, with the first word being the command. 
This supports any [`UnitTypeID`](https://github.com/BurnySc2/python-sc2/blob/develop/sc2/ids/unit_typeid.py) 
or [`UpgradeId`](https://github.com/BurnySc2/python-sc2/blob/develop/sc2/ids/upgrade_id.py) type from python-sc2.

A few extra options are also supported:
```python
class BuildOrderOptions(str, Enum):
    ADDONSWAP = "ADDONSWAP"
    CHRONO = "CHRONO"
    CORE = "CORE"
    GAS = "GAS"
    GATE = "GATE"
    EXPAND = "EXPAND"
    ORBITAL = "ORBITAL"
    SUPPLY = "SUPPLY"
    WORKER = "WORKER"
```

Additionally, strings may contain targets such as `14 pylon @ ramp`, where the last word should contain the target 
command. The following targets are currently supported:
```python
class BuildOrderTargetOptions(str, Enum):
    ENEMY_FOURTH = "ENEMY_FOURTH"
    ENEMY_NAT = "ENEMY_NAT"
    ENEMY_NAT_HG_SPOT = "ENEMY_NAT_HG_SPOT"
    ENEMY_RAMP = "ENEMY_RAMP"
    ENEMY_SPAWN = "ENEMY_SPAWN"
    ENEMY_THIRD = "ENEMY_THIRD"
    FOURTH = "FOURTH"
    MAP_CENTER = "MAP_CENTER"
    NAT = "NAT"
    RAMP = "RAMP"
    SPAWN = "SPAWN"
    THIRD = "THIRD"
```

### Spawning units
Targets may be used to target warp ins, for example:
```yml
- 36 adept @ enemy_nat
```
Will warp in an adept at a power field closest to the enemy natural.
```yml
- 36 marine @ enemy_nat
```
Will prioritize using barracks closest to the enemy natural.

If omitted the default spawn target is our start location.
```yml
# this is perfectly fine
- 36 adept
```

### Chronoboost
If you are using chrono, then the target should contain the structure ID that represents a `UnitTypeID` type, 
for example:

```yml
- 13 chrono @ nexus
- 16 chrono @ gateway
- 20 chrono @ cyberneticscore
```


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
