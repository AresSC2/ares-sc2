![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/AresSC2/ares-sc2?color=brightgreen&sort=semver)
[![Linting](https://github.com/AresSC2/ares-sc2/actions/workflows/lint.yml/badge.svg)](https://github.com/AresSC2/ares-sc2/actions/workflows/lint.yml)
[![Testing](https://github.com/AresSC2/ares-sc2/actions/workflows/test.yml/badge.svg)](https://github.com/AresSC2/ares-sc2/actions/workflows/test.yml)
[![Deploy Documentation](https://github.com/AresSC2/ares-sc2/actions/workflows/pages.yml/badge.svg)](https://github.com/AresSC2/ares-sc2/actions/workflows/pages.yml)

# ares-sc2

[Documentation](https://aressc2.github.io/ares-sc2/index.html)

If you're interested in creating a bot with `ares-sc2` we recommend following the instructions on the
[`ares-sc2-starter-bot` repo](https://github.com/AresSC2/ares-sc2-starter-bot).

Set up environment and mandatory packages to run `ares-sc2`

`poetry install`

Try running the basic test bot, it will place a random race and speed mine with 12 workers:

`poetry run python run.py`

Install optional dependencies for development as needed:
`poetry install --only docs`
`poetry install --only lint`
`poetry install --only test`
`poetry install --only semver`
`poetry install --only notebook`
