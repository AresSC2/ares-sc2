# Ares-SC2 Documentation

<b>Please Note:</b> The documentation while mostly complete, is an ongoing project. 
Please feel free to contribute or raise an issue for anything that is missing.

<b>Useful links:</b> [Installation](./tutorials/installation.html) | [Source Repository](https://github.com/AresSC2/ares-sc2)

## About
`Ares-sc2` is a library that extends the capabilities of the
[python-sc2](https://github.com/BurnySc2/python-sc2) framework. The fundamental principle driving the evolution of 
`ares-sc2` is to empower users with full command over strategic decisions.
Consequently, the library is designed to offer supportive functionalities for bot developers, 
avoiding preconceived choices out of the box. In fact when initiating a project with `ares-sc2`, it closely 
resembles starting with a blank `python-sc2` bot! You can write standard `python-sc2` logic and call upon
`ares` functionality as required.

## Bots made with `ares-sc2`
Feel free to add your own bot here

 - [Phobos (T)](https://github.com/AresSC2/phobos)
 - [QueenBot (Z)](https://github.com/AresSC2/QueenBot)

## Features

 - Highly customizable and extendable behavior system. Curate custom combat maneuvers and macro plans.
 - `ManagerMediator` to facilitate communication and retrieve information from managers in `ares`, 
see [docs here](./api_reference/manager_mediator.html)
 - Memory units tracking by default. Track units that have recently entered fog of war.
 - Pre-calculated building formation for all maps and bases (Terran and Protoss only).
 - [MapAnalyzer](https://github.com/spudde123/SC2MapAnalysis/tree/develop) library available 
via `self.mediator.get_map_data_object`
 - Pathfinding with populated influence grids available as needed.
 - Opt in Build runner system, easily curate new builds via a config file.
 - Data management, set multiple builds via the build runner system and `ares` will cycle through them on defeat.
 - Cython alternatives for common functions.
 - Unit Role management system, a must-have for managing different groups of units.
 - Debug unit spawning at camera location.

## Getting started
<b>New to bot development?</b> We've got you covered! Begin with the
[starter bot installation guide](./tutorials/installation.html) to set up your environment. 
The tutorial provides a blank bot to help you get started. If you're new to
[python-sc2](https://github.com/BurnySc2/python-sc2),
we suggest familiarizing yourself with it first.
Take a look at some examples and documentation on that repository. Remember, you can write python-sc2 code as 
usual within the blank starter bot.
If you're ready to explore features in `ares-sc2`, checking out the [tutorials section](./tutorials) would
be a good next step.

<b>Familiar to bot development and `python-sc2`?</b> Converting your existing bot to `ares-sc2` should be
seamless in most instances, check out the migration guide. Reading through the [tutorials](./tutorials) and
the [api docs]((./api_reference)) should give you an idea of what `ares-sc2` can offer.


## Roadmap

 - Unit squad management and group behaviors
 - Implement more behaviors
 - Add on swapping
 - Placement formation for Zerg
 - Sophisticated build selection system


