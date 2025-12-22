Although `ares-sc2` automatically calculates building formations for all base locations, 
there are situations where precise placement is critical, and custom-building layouts 
are preferred. To address this, `ares-sc2` allows users to specify custom-building positions, 
which are seamlessly integrated into its placement calculations. These custom placements 
are fully compatible with core `ares-sc2` features, such as the Build Runner, `BuildStructure `
behavior, and direct interactions with the building tracker via the `ManagerMediator`. 
Additionally, the system ensures that standard placements within a base location adapt 
to account for user-defined custom positions.

This is a feature only available for Terran and Protoss authors.

> **_Tip:_** When working with custom placements, it is recommended to use the `Debug` flag 
> in your `config.yml` file as well as enabling `ShowBuildingFormation` in `DebugOptions` like so:
```yml
# other config file content ...
Debug: True
DebugOptions:
    ShowBuildingFormation: True
```

This will help you visualize the placement of your structures on the map. White cuboids represent
custom placements, while any other colour represents placements calculated by `ares-sc2`.

## Defining custom placements
Create a file in the root of your bot folder named `<bot_race>_building_placements.yml`, you should enter placements
into this file like below. All entries are optional, and if not specified, ares-sc2 will use default values 
in its own file or search for calculated alternatives.

Here is an example of a `protoss_building_placements.yml` file defining natural wall placements for Protoss vs Zerg.

```yml
Persephone:
  UpperSpawn:
    VsZerg:
      FirstPylon:
        # natural wall
        - [ [ 69.0, 144.0 ] ]
      PylonsWall:
        # natural wall
        - [ [ 71.0, 145.0 ] ]
      ThreeByThreesWall:
        # natural wall
        - [ [ 71.5, 138.5 ], [ 73.5, 142.5 ], [ 74.5, 145.5 ] ]
      StaticDefencesWall:
        # natural wall
        - [ [ 68.0, 140.0 ] ]
      GateKeeper:
        # natural wall
        - [ [ 72.5, 140.5 ] ]
  LowerSpawn:
    VsZerg:
      FirstPylon:
        # natural wall
        - [ [ 69.0, 36.0 ] ]
      PylonsWall:
        # natural wall
        - [ [ 71.0, 39.0 ] ]
      ThreeByThreesWall:
        # natural wall
        - [ [ 74.5, 35.5 ], [ 72.5, 39.5 ], [ 69.5, 41.5 ] ]
      StaticDefencesWall:
        # natural wall
        - [ [ 68.0, 38.0 ] ]
      GateKeeper:
        # natural wall
        - [ [ 73.5, 37.5 ] ]
```

> **_Tip:_** If you don't want to define placements for all races individually, you can use the `VsAll` key.

> **_Tip:_** 2x2 placements should be placed at rounded coordinates eg `[ [ 71.0, 138.0 ] ]`
> And 3x3 placements should be placed at coordinates ending with `0.5` eg `[ [ 74.5, 135.5 ], [ 72.5, 139.5 ] ]`

Note there is no need to specify the base location placements belong to, `ares-sc2` will automatically 
calculate them based on the position passed in.

Now let's look at an example of a `terran_building_placements.yml` file where we highlight different 
ways of defining placements. Ignore the actual dummy positions shown here, they are just for illustration purposes.

```yaml
Pylon:
  UpperSpawn:
    # VsAll means placements apply to all races
    VsAll:
      # we can define placements all in line like this
      BunkersWall: [[ 147.5, 78.5 ]]
      MissileTurrets: [[ 172.0, 88.0 ]]
      Production: [[ 170.5, 92.5], [ 165.5, 92.5], [ 160.5, 92.5]]
      UpgradeStructures: [[ 170.5, 89.5], [ 165.5, 89.5]]
      SensorTowers: [[ 169.0, 90.0], [ 165.5, 89.5]]
      # or make a list of lists if you want 
      # to organize placements using comments
      SupplyDepots:
        # main base
        - [[ 169.0, 82.0 ], [ 170.0, 54.0 ], [ 171.0, 86.0 ]]
        # natural
        - [[ 138.0, 76.0 ]]
      SupplyDepotsWall:
        - [[ 166.0, 90.0 ], [ 166.0, 92.0 ]]
    # race specific placements can be defined separately
    # these take priority over the VsAll placements
    VsZerg:
      Production: [[ 166.5, 92.5], [ 163.5, 92.5], [ 160.5, 92.5]]
      SupplyDepots:
        # main base
        - [[ 170.0, 92.0 ], [ 171.0, 92.0 ]]
        # natural
        - [[ 138.0, 76.0 ]]
      SupplyDepotsWall: [[ 166.0, 90.0 ], [ 166.0, 92.0 ]]
    VsProtoss:
      SupplyDepots: [ [ 105.0, 170.0 ] ]
    VsTerran:
      SupplyDepots: [ [ 105.0, 170.0 ] ]
    VsRandom:
      SupplyDepots: [ [ 105.0, 170.0 ] ]
  LowerSpawn:
    VsAll:
      BunkersWall: [[ 147.5, 78.5 ]]
      MissileTurrets: [[ 172.0, 88.0 ]]
      Production: [[ 170.5, 92.5], [ 165.5, 92.5], [ 160.5, 92.5]]
      UpgradeStructures: [[ 170.5, 89.5], [ 165.5, 89.5]]
      SensorTowers: [[ 169.0, 90.0], [ 165.5, 89.5]]
      SupplyDepots:
        # main base
        - [[ 169.0, 82.0 ], [ 170.0, 54.0 ], [ 171.0, 86.0 ]]
        # natural
        - [[ 138.0, 76.0 ]]
      SupplyDepotsWall:
        - [[ 166.0, 90.0 ], [ 166.0, 92.0 ]]
    VsZerg:
      Production: [[ 166.5, 92.5], [ 163.5, 92.5], [ 160.5, 92.5]]
      SupplyDepots:
        # main base
        - [[ 170.0, 92.0 ], [ 171.0, 92.0 ]]
        # natural
        - [[ 138.0, 76.0 ]]
      SupplyDepotsWall: [[ 166.0, 90.0 ], [ 166.0, 92.0 ]]
    VsProtoss:
      SupplyDepots: [ [ 105.0, 170.0 ] ]
    VsTerran:
      SupplyDepots: [ [ 105.0, 170.0 ] ]
    VsRandom:
      SupplyDepots: [ [ 105.0, 170.0 ] ]

```

If you want to define placements in a compact manner, define the list inline like so:
```yml
SupplyDepots: [ [ 105.0, 170.0 ] ]
```

Though it might be useful to organise placements with comments, so you could also define it like this:
```yml
SupplyDepots:
# main base
- [[ 170.0, 92.0 ], [ 171.0, 92.0 ]]
# natural
- [[ 138.0, 76.0 ]]
```


`ares-sc2` does contain some default natural wall placements for Protoss vs Zerg for 
some maps. You can view the internal file inside the `ares-sc2/src/ares/` directory.

However, you can override any of 
these settings by creating your own `<bot_race>_building_placements.yml` file and specifying 
only the elements you wish to change. `ares-sc2` will automatically prioritize 
your custom placements and fill in any missing elements with the default values.

This is an example content of a `protoss_building_placements.yml`
file where the first pylon position on Persephone is tweaked.
```yml
Persephone:
    UpperSpawn:
        FirstPylon: [ [ 68.0, 143.0 ] ]
    LowerSpawn:
        FirstPylon: [ [ 68.0, 36.0 ] ]
```

When creating your building placements file, ensure the keys are spelled correctly and match the example
above. Internally `ares-sc2` checks an `Enum` similar to this when parsing the file:
```python
class BuildingPlacementOptions(str, Enum):
    BUNKERS = "Bunkers"
    BUNKERS_WALL = "BunkersWall"
    FIRST_PYLON = "FirstPylon"
    GATE_KEEPER = "GateKeeper"
    LOWER_SPAWN = "LowerSpawn"
    MISSILE_TURRETS = "MissileTurrets"
    PRODUCTION = "Production"
    PRODUCTION_WALL = "ProductionWall"
    PYLONS = "Pylons"
    PYLONS_WALL = "PylonsWall"
    SENSOR_TOWERS = "SensorTowers"
    STATIC_DEFENCES = "StaticDefences"
    STATIC_DEFENCES_WALL = "StaticDefencesWall"
    SUPPLY_DEPOTS = "SupplyDepots"
    SUPPLY_DEPOTS_WALL = "SupplyDepotsWall"
    THREE_BY_THREES = "ThreeByThrees"
    THREE_BY_THREES_WALL = "ThreeByThreesWall"
    UPPER_SPAWN = "UpperSpawn"
    UPGRADE_STRUCTURES = "UpgradeStructures"
    UPGRADE_STRUCTURES_WALL = "UpgradeStructuresWall"
    VS_ALL = "VsAll"
    VS_PROTOSS = "VsProtoss"
    VS_RANDOM = "VsRandom"
    VS_TERRAN = "VsTerran"
    VS_ZERG = "VsZerg"
```

### Providing impossible placements
`ares-sc2` validates your placements before adding them internally. If an invalid placement is detected, 
an error message will be logged, but your bot will continue running as normal. If your placements 
aren’t working as expected, be sure to check the logs for more details.

### WARNING!
Ensure care is taken when defining placements, try to leave room for addons and prevent
blocking in units.

## Retrieve gate keeper placements
In Protoss vs Zerg this is the gap in the natural wall that is usually blocked by a 
gateway unit. Keep in mind this could be `None` if no position is provided for the
current map.

```python
nat_gatekeeper_position: Point2 | None = self.mediator.get_nat_gatekeeper_position
```

The system is flexible enough to handle multiple gatekeepers though. You can retrieve the 
internal dictionary `ares` uses:
```python
# key is expansion location, value is list of gatekeepers
gatekeeper_positions: dict[Point2, list[Point2]] = self.mediator.get_gatekeeper_positions
```


## Using custom placements with ares
There are several ways these placements can be utilized.

### Via the BuildRunner
See [build Runner tutorial](../tutorials/build_runner.md) if you're unfamiliar.

Below is an example of a valid build order that places structures at the natural wall or the reaper wall. 
To specify that a structure should use your custom natural wall placements or reaper wall placements, simply 
add `@ nat_wall` or `@ reaper_wall` when declaring a build step. If the map has no custom placements or 
all available positions are already taken, the build runner will automatically find a 
suitable alternative nearby.

```yml
UseData: True
# How should we choose a build? Cycle is the only option for now
BuildSelection: Cycle
# For each Race / Opponent ID choose a build selection
BuildChoices:
    # test_123 is active if Debug: True (set via a `config.yml` file)
    test_123:
        BotName: Test
        Cycle:
            - DummyBuild

    Protoss:
        BotName: ProtossRace
        Cycle:
            - DummyBuild

    Random:
        BotName: RandomRace
        Cycle:
            - DummyBuild

    Terran:
        BotName: TerranRace
        Cycle:
            - DummyBuild

    Zerg:
        BotName: ZergRace
        Cycle:
            - DummyBuild


Builds:
    DummyBuild:
        ConstantWorkerProductionTill: 44
        AutoSupplyAtSupply: 23
        OpeningBuildOrder:
            - 14 pylon @ nat_wall
            - 15 gate @ nat_wall
            - 16 gate @ nat_wall
            - 16 core @ nat_wall
            - 16 pylon @ nat_wall
            - 16 shieldbattery @ nat_wall
            # build the reaper wall
            - 16 pylon @ reaper_wall
            - 16 gate @ reaper_wall
            - 16 gate @ reaper_wall

```

### `BuildStructure` behavior
You can build wall structures within your own bot logic via the 
[`BuildStructure` behavior](../api_reference/behaviors/macro_behaviors.md#ares.behaviors.macro.build_structure.BuildStructure).
If wall placements are not available this will look for a closely alternative. Remember here
you need to pass in the correct expansion location to pick up the custom placements for that base.
Some examples:

```python
from sc2.ids.unit_typeid import UnitTypeId

# attempt to build two gateway and cybernetics core at the natural wall
self.register_behavior(
    BuildStructure(
        base_location=self.mediator.get_own_nat,
        structure_id=UnitTypeId.GATEWAY,
        wall=True,
        to_count_per_base=2
    )
)
self.register_behavior(
    BuildStructure(
        base_location=self.mediator.get_own_nat,
        structure_id=UnitTypeId.CYBERNETICSCORE,
        wall=True,
        to_count_per_base=1
    )
)

# terran wants to use depot placements they specify in their own file
# They should use `supply_depot=True`
self.register_behavior(
    BuildStructure(
        base_location=self.start_location,
        structure_id=UnitTypeId.SUPPLYDEPOT,
        supply_depot=True,
    )
)

# terran wants to build 3 missile turrets at the third
# using the placements they specify in their own file
self.register_behavior(
    BuildStructure(
        base_location=self.mediator.get_defensive_third,
        structure_id=UnitTypeId.MISSILETURRET,
        missile_turret=True,
        to_count_per_base=3
    )
)
```

### Via the `ManagerMediator`
For more customized control you can interact with the wall placements via the `mediator`. See
some examples below.

Get the first pylon placement without reserving placement in the building tracker:

```python
from sc2.ids.unit_typeid import UnitTypeId

if placement := mediator.request_building_placement(
        base_location=self.mediator.get_own_nat,
        structure_type=UnitTypeId.PYLON,
        first_pylon=self.first_pylon,
        reserve_placement=False
    ):
    pass
```

Work directly with the raw data, example here gets the natural wall placements.

```python
from ares.consts import BuildingSize
from sc2.position import Point2

placements_dict: dict[Point2, dict[BuildingSize, dict]] = self.mediator.get_placements_dict
natural_placements: dict[BuildingSize, dict] = placements_dict[self.mediator.get_own_nat]

two_by_twos_at_wall: list[Point2] = [
            placement
            for placement in natural_placements[BuildingSize.TWO_BY_TWO]
            if natural_placements[BuildingSize.TWO_BY_TWO][placement]["is_wall"]
        ]

three_by_threes_at_wall: list[Point2] = [
            placement
            for placement in natural_placements[BuildingSize.TWO_BY_TWO]
            if natural_placements[BuildingSize.THREE_BY_THREE][placement]["is_wall"]
        ]
```

Get all production placements in the main base:

```python
from ares.consts import BuildingSize
from sc2.position import Point2

placements_dict: dict[Point2, dict[BuildingSize, dict]] = self.mediator.get_placements_dict
main_base_placements: dict[BuildingSize, dict] = placements_dict[self.start_location]

production_placements: list[Point2] = [
            placement
            for placement in main_base_placements[BuildingSize.THREE_BY_THREE]
            if natural_placements[BuildingSize.THREE_BY_THREE][placement]["production"]
        ]
```

