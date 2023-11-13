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

## Setting up `ares-sc2`

To setup a full development environment:

`poetry install --with docs,lint,test,semver,notebook`

To set up just the core packages to run an `AresBot`

`poetry install`

Try running the basic test bot, it will place a random race and speed mine with 12 workers:

`poetry run python run.py`

Install optional dependencies only as needed, for example:

`poetry install --only docs`
