Although ares-sc2 automatically calculates building formations for all base locations, 
there are situations where precise placement is critical, and custom-building layouts 
are preferred. To address this, ares-sc2 allows users to specify custom-building positions, 
which are seamlessly integrated into its placement calculations. These custom placements 
are fully compatible with core `ares-sc2` features, such as the Build Runner, `BuildStructure `
behavior, and direct interactions with the building tracker via the `ManagerMediator`. 
Additionally, the system ensures that standard placements within a base location adapt 
to account for user-defined custom positions.

At present, custom placements are supported exclusively for Protoss vs. Zerg natural wall setups. 
Support for additional scenarios will be introduced in future updates.

## Defining custom placements
Create a file in the root of your bot folder names `building_placements.yml`, you should enter placements
into this file like below.

```yml
Protoss:
    AbyssalReef:
        VsZergNatWall:
            AvailableVsRaces: ["Zerg", "Random"]
            UpperSpawn:
                FirstPylon: [[64., 105.]]
                Pylons: [[63., 112.]]
                ThreeByThrees: [[68.5, 109.5], [66.5, 106.5], [60.5, 106.5]]
                StaticDefences: [[64., 110.]]
                GateKeeper: [[62.25, 105.86]]
            LowerSpawn:
                FirstPylon: [[136., 39.]]
                Pylons: [[137., 32.]]
                ThreeByThrees: [[131.5, 34.5], [133.5, 37.5], [139.5, 37.5]]
                StaticDefences: [[136., 36.]]
                GateKeeper: [[137.25, 38.6]]
    Acropolis:
        VsZergNatWall:
            AvailableVsRaces: ["Zerg", "Random"]
            UpperSpawn:
                FirstPylon: [ [ 35., 109. ] ]
                Pylons: [ [ 32., 109. ] ]
                ThreeByThrees: [ [ 38.5, 106.5 ], [ 34.5, 105.5 ], [ 31.5, 105.5 ] ]
                StaticDefences: [ [ 39., 109. ] ]
                GateKeeper: [ [ 36.6, 105.6 ] ]
            LowerSpawn:
                FirstPylon: [ [ 141., 63. ] ]
                Pylons: [ [ 144., 63. ] ]
                ThreeByThrees: [ [ 137.5, 66.5 ], [ 141.5, 66.5 ], [ 144.5, 66.5 ] ]
                StaticDefences: [ [ 137., 63. ] ]
                GateKeeper: [ [ 139.3, 67.4 ] ]
    Automaton:
        VsZergNatWall:
            AvailableVsRaces: ["Zerg", "Random"]
            UpperSpawn:
                FirstPylon: [ [ 141., 139. ] ]
                Pylons: [ [ 140., 142. ] ]
                ThreeByThrees: [ [ 138.5, 133.5 ], [ 136.5, 137.5 ], [ 136.5, 140.5 ] ]
                StaticDefences: [ [ 142., 136. ] ]
                GateKeeper: [ [ 136.9, 135.6 ] ]
            LowerSpawn:
                FirstPylon: [ [ 43., 42. ] ]
                Pylons: [ [ 44., 39. ] ]
                ThreeByThrees: [ [ 45.5, 46.5 ], [ 47.5, 42.5 ], [ 47.5, 39.5 ] ]
                StaticDefences: [ [ 42., 45. ] ]
                GateKeeper: [ [ 47.15, 45.3 ] ]
    Ephemeron:
        VsZergNatWall:
            AvailableVsRaces: ["Zerg", "Random"]
            UpperSpawn:
                FirstPylon: [ [ 37., 112. ] ]
                Pylons: [ [ 37., 109. ] ]
                ThreeByThrees: [ [ 42.5, 114.5 ], [ 42.5, 110.5 ], [ 41.5, 107.5 ] ]
                StaticDefences: [ [ 38., 115. ] ]
                GateKeeper: [ [ 43.1, 112.58 ] ]
            LowerSpawn:
                FirstPylon: [ [ 125., 49. ] ]
                Pylons: [ [ 125., 52. ] ]
                ThreeByThrees: [ [ 120.5, 45.5 ], [ 120.5, 49.5 ], [ 120.5, 52.5 ] ]
                StaticDefences: [ [ 125., 46. ] ]
                GateKeeper: [ [ 119.7, 47.4 ] ]
    Interloper:
        VsZergNatWall:
            AvailableVsRaces: ["Zerg", "Random"]
            UpperSpawn:
                FirstPylon: [ [ 31., 112. ] ]
                Pylons: [ [ 31., 109. ] ]
                ThreeByThrees: [ [ 35.5, 114.5 ], [ 35.5, 110.5 ], [ 35.5, 107.5 ] ]
                StaticDefences: [ [ 31., 115. ] ]
                GateKeeper: [ [ 36.16, 112.68 ] ]
            LowerSpawn:
                FirstPylon: [ [ 121., 56. ] ]
                Pylons: [ [ 121., 59. ] ]
                ThreeByThrees: [ [ 116.5, 53.5 ], [ 116.5, 57.5 ], [ 116.5, 60.5 ] ]
                StaticDefences: [ [ 121., 53. ] ]
                GateKeeper: [ [ 115.78, 55.75 ] ]
    Thunderbird:
        VsZergNatWall:
            AvailableVsRaces: ["Zerg", "Random"]
            UpperSpawn:
                FirstPylon: [ [ 46., 106. ] ]
                Pylons: [ [ 46., 103. ] ]
                ThreeByThrees: [ [ 50.5, 109.5 ], [ 50.5, 105.5 ], [ 50.5, 102.5 ] ]
                StaticDefences: [ [ 46., 109. ] ]
                GateKeeper: [ [ 51.18, 107.67 ] ]
            LowerSpawn:
                FirstPylon: [ [ 144., 51 ] ]
                Pylons: [ [ 144., 54. ] ]
                ThreeByThrees: [ [ 139.5, 46.5 ], [ 139.5, 50.5 ], [ 139.5, 53.5 ] ]
                StaticDefences: [ [ 144., 48. ] ]
                GateKeeper: [ [ 138.64, 48.49 ] ]


```

The values shown above are the default settings in ares, so there's no need to 
create your own file if you're satisfied with them. However, you can customize 
these settings by creating your own building_placements.yml file and specifying 
only the elements you wish to change. ares-sc2 will automatically prioritize 
your custom placements and fill in any missing elements with the default values.

This is an example contents of a `building_placements.yml`
file where the first pylon position on Thunderbird is tweaked.
```yml
    Thunderbird:
        VsZergNatWall:
            UpperSpawn:
                FirstPylon: [ [ 47., 107. ] ]
            LowerSpawn:
                FirstPylon: [ [ 143., 52 ] ]
```

When creating your building placements file, ensure the keys are spelled correctly and match the example
above. Internally `ares-sc2` checks an `Enum` similar to this when parsing the file:
```python
class BuildingPlacementOptions(str, Enum):
    LOWER_SPAWN = "LowerSpawn"
    UPPER_SPAWN = "UpperSpawn"
    VS_ZERG_NAT_WALL = "VsZergNatWall"
    FIRST_PYLON = "FirstPylon"
    PYLONS = "Pylons"
    THREE_BY_THREES = "ThreeByThrees"
    STATIC_DEFENCES = "StaticDefences"
    GATE_KEEPER = "GateKeeper"
```

### Providing impossible placements
`ares-sc2` validates your placements before adding them internally. If an invalid placement is detected, 
an error message will be logged, but your bot will continue running as normal. If your placements 
aren’t working as expected, be sure to check the logs for more details.

## Retrieve the gate keeper placement
In Protoss vs Zerg this is the gap in the natural wall that is usually blocked by a 
gateway unit. Keep in mind this could be `None` if no position is provided for the
current map.

```python
nat_wall_gatekeeper_pos: Union[Point2, None] = self.mediator.get_pvz_nat_gatekeeping_pos
```

## Using custom placements with ares
There are several ways these placements can be utilized.

### Via the BuildRunner
See [build Runner tutorial](../tutorials/build_runner.md) if you're unfamiliar.

Below is an example of a valid build order that places structures at the natural wall. 
To specify that a structure should use your custom natural wall placements, simply 
add `@ nat_wall` when declaring a build step. If the map has no custom placements or 
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
            - NatWall

    Protoss:
        BotName: ProtossRace
        Cycle:
            - NatWall

    Random:
        BotName: RandomRace
        Cycle:
            - NatWall

    Terran:
        BotName: TerranRace
        Cycle:
            - NatWall

    Zerg:
        BotName: ZergRace
        Cycle:
            - NatWall


Builds:
    NatWall:
        ConstantWorkerProductionTill: 44
        AutoSupplyAtSupply: 23
        OpeningBuildOrder:
            - 14 pylon @ nat_wall
            - 15 gate @ nat_wall
            - 16 gate @ nat_wall
            - 16 core @ nat_wall
            - 16 pylon @ nat_wall
            - 16 shieldbattery @ nat_wall
```

### `BuildStructure` behavior
You can build wall structures within your own bot logic via the 
[`BuildStructure` behavior](../api_reference/behaviors/macro_behaviors.md#ares.behaviors.macro.build_structure.BuildStructure).
If wall placements are not available this will look for a closely alternative. Ensure
`base_location=self.mediator.get_own_nat` to ensure natural wall is found.
See example code:

```python
from sc2.ids.unit_typeid import UnitTypeId

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
self.register_behavior(
    BuildStructure(
        base_location=self.mediator.get_own_nat,
        structure_id=UnitTypeId.PYLON,
        wall=True,
        to_count_per_base=2
    )
)
self.register_behavior(
    BuildStructure(
        base_location=self.mediator.get_own_nat,
        structure_id=UnitTypeId.SHIELDBATTERY,
        wall=True,
        to_count_per_base=1
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

