![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/AresSC2/ares-sc2?color=brightgreen&sort=semver)
[![Linting](https://github.com/AresSC2/ares-sc2/actions/workflows/lint.yml/badge.svg)](https://github.com/AresSC2/ares-sc2/actions/workflows/lint.yml)
[![Testing](https://github.com/AresSC2/ares-sc2/actions/workflows/test.yml/badge.svg)](https://github.com/AresSC2/ares-sc2/actions/workflows/test.yml)
[![Deploy Documentation](https://github.com/AresSC2/ares-sc2/actions/workflows/pages.yml/badge.svg)](https://github.com/AresSC2/ares-sc2/actions/workflows/pages.yml)

# ares-sc2

[Documentation](https://aressc2.github.io/ares-sc2/index.html)

If you're interested in creating a bot with `ares-sc2` we recommend following the instructions on the
[`ares-sc2-starter-bot` repo](https://github.com/AresSC2/ares-sc2-starter-bot).

## About
`Ares-sc2` is a library that extends the capabilities of the
[python-sc2](https://github.com/BurnySc2/python-sc2) framework. The fundamental principle driving the evolution of 
`ares-sc2` is to empower users with full command over strategic decisions.
Consequently, the library is designed to offer supportive functionalities for bot developers, 
avoiding preconceived choices out of the box. In fact when initiating a project with `ares-sc2`, it closely 
resembles starting with a blank `python-sc2` bot! You can write standard `python-sc2` logic and call upon
`ares` functionality as required.

## Features

 - Optimized cython functions via the [cython-extensions-sc2 library](https://github.com/AresSC2/cython-extensions-sc2).
 - Calculated production formation for every expansion location on game start for Terran and Protoss, 
use convenience behavior `BuildStructure` for easy usage.
```python
from ares.behaviors.macro import BuildStructure
from sc2.ids.unit_typeid import UnitTypeId

self.register_behavior(
    BuildStructure(
        base_location=self.start_location,
        structure_id=UnitTypeId.BARRACKS
    )
)
```
![protoss](https://github.com/user-attachments/assets/31a2cbf1-a95b-492c-89eb-563013cc6b75)

 - Various grids with populated enemy influence.

 - Curate custom combat maneuvers with our plug and play behavior system. Mix and match your own
behaviors to truly create some unique play styles! Individual and Group behaviors are now available.
```python
from ares import AresBot
from ares.behaviors.combat import CombatManeuver
from ares.behaviors.combat.individual import (
    DropCargo,
    KeepUnitSafe,
    PathUnitToTarget,
    PickUpCargo,
)
from sc2.unit import Unit
from sc2.units import Units
import numpy as np

class MyBot(AresBot):
    async def on_step(self, iteration: int) -> None:
        # retrieve medivac and mines_to_pickup and pass to method
        # left out here for clarity
        # mines would require their own behavior
        self.do_medivac_mine_drop(medivac, mines_to_pickup)

    def do_medivac_mine_drop(
            self, 
            medivac: Unit, 
            mines_to_pickup: Units
    ) -> None:
        # initialize a new CombatManeuver
        mine_drop: CombatManeuver = CombatManeuver()
        # get a grid for the medivac to path on
        air_grid: np.ndarray = self.mediator.get_air_grid
        # first priority is picking up units
        mine_drop.add(
            PickUpCargo(
                unit=medivac, 
                grid=air_grid, 
                pickup_targets=mines_to_pickup)
        )
        # if there is cargo, path to target and drop them off
        if medivac.has_cargo:
            # path
            mine_drop.add(
                PathUnitToTarget(
                    unit=medivac,
                    grid=air_grid,
                    target=self.enemy_start_locations[0],
                )
            )
            # drop off the mines
            mine_drop.add(
                DropCargo(unit=medivac, target=medivac.position)
            )
        # no cargo and no units to pick up, stay safe
        else:
            mine_drop.add(
                KeepUnitSafe(unit=medivac, grid=air_grid)
            )

        # finally register this maneuver to be executed
        self.register_behavior(mine_drop)
```
 - Convenient production management via `SpawnController` and `ProductionController` behaviors.
 - [MapAnalyzer](https://github.com/spudde123/SC2MapAnalysis) library available and used throughout `ares-sc2`,
access the library yourself via `self.mediator.get_map_data_object`

 - [CombatSim](https://github.com/danielvschoor/sc2-helper) helper method available via `self.mediator.can_win_fight`
 - Opt in Build runner system, easily curate new builds via a yml config file.

 - Use `KDTree` for fast distance checks on batches of units, example:
```python
from ares.consts import UnitTreeQueryType

from sc2.ids.unit_typeid import UnitTypeId
from sc2.unit import Unit
from sc2.units import Units

reapers: list[Unit] = self.mediator.get_own_units_dict[UnitTypeId.REAPER]
all_ground_near_reapers: dict[int, Units] = self.mediator.get_units_in_range(
    start_points=reapers,
    distances=15,
    query_tree=UnitTreeQueryType.EnemyGround,
    return_as_dict=True,
)

for reaper in reapers:
    near_ground: Units = all_ground_near_reapers[reaper.tag]
```

 - `ares-sc2` works quietly behind the scenes, yet at any moment access to a wealth of information
is available via the `mediator`, some examples:

Retrieve a ground pathing grid already containing enemy influence:

`grid: np.ndarray = self.mediator.get_ground_grid`

Use this grid to make a pathing call:

`move_to: Point2 = self.mediator.find_path_next_point(start=unit.position, target=self.target, grid=grid)`

Optimally select a worker and assign a new `UnitRole`:
```python
from ares.consts import UnitRole
from sc2.ids.unit_typeid import UnitTypeId
from sc2.units import Units

if worker := self.mediator.select_worker(target_position=self.main_base_ramp.top_center):
    self.mediator.assign_role(tag=worker.tag, role=UnitRole.DEFENDING)

# retrieve `UnitRole.DEFENDING` workers
defending_workers: Units = self.mediator.get_units_from_role(
    role=UnitRole.DEFENDING, unit_type=UnitTypeId.SCV
)
```

See [Manager Mediator docs](https://aressc2.github.io/ares-sc2/api_reference/manager_mediator.html) for all
available methods.

## Setting up `ares-sc2`

To setup a full development environment:

`poetry install --with docs,lint,test,semver,notebook`

To set up just the core packages to run an `AresBot`

`poetry install`

Try running the basic test bot, it will place a random race and speed mine with 12 workers:

`poetry run python run.py`

Install optional dependencies only as needed, for example:

`poetry install --only docs`

## Contributing to the docs
It's possible to set up a lightweight environment that only sets up requirements for testing 
the documentation locally. As a prerequisite [poetry](https://python-poetry.org/) should 
be installed on your system. `pip install poetry` is probably all you need in most instances.

1. Fork and then Clone the repo
`git clone <repo-url>`

2. Setup environment and install docs requirements
`poetry install --only docs`

3. Run the documentation in a live local webserver
`poetry run mkdocs serve`

4. Visit `http://127.0.0.1:8000/` using your favourite web browser.

5. Edit `.md` files in the `docs` directory, and any saved changes will automatically be reloaded in your browser.

The documentation relies on the [MkDocs](https://www.mkdocs.org/) library to generate the docs. 
To automatically generate API docs from code we use the [mkdocstrings extension](https://mkdocstrings.github.io/) .

See `mkdocs.yml` file for settings and for configuring the navigation bars.

