
## Build Runner System
The Build Runner System is a tool that enables swift build prototyping through a configuration file. 
Optional data usage can be incorporated to maintain build history. IMPORTANT: The build runner system
is designed only for curating optimized build orders in the first few minutes of the game. Your bot 
should switch to dynamic behavior after completion, checked via ```self.build_order_runner.build_completed```.

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

Further to this, be careful adding steps where units require morphing from other units. If you
want banelings then it's up to the author to ensure zerglings are around. If you require an Archon
then two templar should exist to ensure the morph is successful. The build runner will not fill
in the gaps for you.


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
    OVERLORD_SCOUT = "OVERLORD_SCOUT"
    SUPPLY = "SUPPLY"
    WORKER = "WORKER"
    WORKER_SCOUT = "WORKER_SCOUT"
```

Additionally, strings may contain targets such as `14 pylon @ ramp`, where the last word should contain the target 
command. The following targets are currently supported:
```python
class BuildOrderTargetOptions(str, Enum):
    ENEMY_FOURTH = "ENEMY_FOURTH"
    ENEMY_NAT = "ENEMY_NAT"
    ENEMY_NAT_HG_SPOT = "ENEMY_NAT_HG_SPOT"
    ENEMY_NAT_VISION = "ENEMY_NAT_VISION"
    ENEMY_RAMP = "ENEMY_RAMP"
    ENEMY_SPAWN = "ENEMY_SPAWN"
    ENEMY_THIRD = "ENEMY_THIRD"
    FIFTH = "FIFTH"
    FOURTH = "FOURTH"
    MAP_CENTER = "MAP_CENTER"
    NAT = "NAT"
    RAMP = "RAMP"
    SIXTH = "SIXTH"
    SPAWN = "SPAWN"
    THIRD = "THIRD"
```

### AutoSupply (optional)
Automatically handle building supply structures after the supply set.
Enable AutoSupply in your build order at a specific supply count. 
This example turns on AutoSupply after 17 supply so you no longer need to declare supply
structures in your build:
```yml
Builds:
    DummyBuild:
        # After 17 supply turn AutoSupply on
        AutoSupplyAtSupply: 17
        ConstantWorkerProductionTill: 50
        OpeningBuildOrder:
            - 14 pylon @ ramp
            - 15 worker_scout:
                [spawn, nat, enemy_spawn, third, fourth, map_center, enemy_nat]
            - 16 gate
            - 16 gas
            - 17 gas
            - 19 gate
            - 20 core
            - 22 adept x2
            - 25 stargate
```

### Automatic worker production (optional)
Like AutoSupply, this cleans up your build order. Use `ConstantWorkerProductionTill` to set an integer value:

```yml
Builds:
    ProbeMaxout:
        # After 0 supply turn AutoSupply on
        AutoSupplyAtSupply: 0
        ConstantWorkerProductionTill: 200
        OpeningBuildOrder:
            - 200 gateway
```

### Build complete
Upon completion of the build, a typical bot workflow should allow for dynamic production. To check whether the opening 
has been completed or not, you can use the following method call:

```python
self.build_order_runner.build_completed
```

#### Set build complete
You can set the build to be complete at any time using the following:
```python
self.build_order_runner.set_build_completed()
```

### Chronoboost
For chrono, target structures using UnitTypeID, e.g.:

```yml
- 13 chrono @ nexus
- 16 chrono @ gateway
- 20 chrono @ cyberneticscore
```

### Duplicate commands
Use `x`, `X`, or `*` followed by an integer to duplicate commands. Ensure sufficient supply.
And consider turning `AutoSupply` option on if using duplicate commands.


Examples:
```yml
- 12 worker x3
```

```yml
- 12 pylon @ ramp *5
```

```yml
- 15 barracks ramp *2
```

```yml
- 42 roach *16
```

### Retrieve the opening build name
Retrieve the opening build name using the following method call:

```self.build_order_runner.chosen_opening```

This method will return a string value containing the name of the currently selected build from the 
`<my_race_lowercase>_builds.yml` file.

### Scouting
`worker_scout` and `overlord_scout` options are currently available.

#### Simple worker scout
Use `worker_scout` to scout the enemy base:
```yml
Builds:
    DummyBuild:
        OpeningBuildOrder:
            - 12 worker_scout
```

#### Advanced worker scout
Provide locations via a list for the worker to scout:
```yml
Builds:
    DummyBuild:
        OpeningBuildOrder:
            - 12 worker_scout:
                  [spawn, nat, enemy_spawn, third, fourth, map_center, enemy_nat]
```

See `BuildOrderTargetOptions` above for all valid options.

#### Overlord scout
Use `overlord_scout` command to send overlord to scout. Unlike the worker scout
there is no default behavior so please provide locations.
See example below, overlord checks enemy natural, then finds a close high ground spot.
```yml
Builds:
    DummyBuild:
        OpeningBuildOrder:
            - 12 overlord_scout:
                  [enemy_nat_vision, enemy_nat_hg_spot]
```

See `BuildOrderTargetOptions` above for all valid options.

#### Taking control of scouts
Take the following scenario: Your worker scout has found a proxy, and you want to harass the enemy scv.
The build runner takes no opinion how your scout should handle this scenario, but you can grab control
of the worker and issue your own commands. Internally `ares-sc2` assigns scouts to the `BUILD_RUNNER_SCOUT`
 `UnitRole`, so we can grab the scout via the mediator like so:

```python
worker_scouts: Units = self.mediator.get_units_from_role(
    role=UnitRole.BUILD_RUNNER_SCOUT, unit_type=self.worker_type
)
for scout in worker_scouts:
    # issue custom commands
    pass
```

You can retrieve overlord scouts in a similar manner.

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

### Switch openings on the fly
It's possible to switch openings on the fly, `ares` will attempt to work out
which build steps have already completed and find a reasonable point in the
new build order to resume from.

You should pass a valid opening name from your builds yaml file, something like:
```python
if self.opponent_is_cheesing:
    self.build_order_runner.switch_opening("DefensiveOpening")
```
Note that if an incorrect opening name is passed here the bot will terminate.
