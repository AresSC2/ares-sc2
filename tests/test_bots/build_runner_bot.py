from __future__ import annotations

import random
import sys
from os import environ
from os.path import abspath, dirname, isabs, join

import yaml
from loguru import logger
from sc2 import maps
from sc2.data import Difficulty, Race
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId
from sc2.main import run_game
from sc2.player import Bot, Computer

# Get the directory of the current file
current_dir = dirname(__file__)

# Go two directories up
two_up = abspath(join(current_dir, "..", ".."))

# Append the src folder to the path
src_path = join(two_up, "src")

# Add the src folder to the system path
sys.path.append(src_path)

from ares import AresBot
from ares.behaviors.macro import Mining
from ares.consts import ALL_STRUCTURES, BUILDS

DEFAULT_BUILD_RUNNER_RACE: str = "Protoss"


def _configured_build_runner_race() -> Race:
    race_name: str = environ.get("BUILD_RUNNER_RACE", DEFAULT_BUILD_RUNNER_RACE).title()
    try:
        return Race[race_name]
    except KeyError as e:
        raise ValueError(
            "BUILD_RUNNER_RACE must be one of: Terran, Protoss, Zerg"
        ) from e


def _configured_builds_file(race: Race) -> str:
    builds_file: str | None = environ.get("BUILD_RUNNER_BUILDS_FILE")
    if builds_file:
        return builds_file if isabs(builds_file) else join(two_up, builds_file)

    return join(
        two_up,
        "examples",
        "build_runner_examples",
        f"{race.name.lower()}_builds.yml",
    )


BUILD_RUNNER_RACE: Race = _configured_build_runner_race()
BUILDS_FILE: str = _configured_builds_file(BUILD_RUNNER_RACE)
# If a build hasn't completed after this much game time (seconds), treat
# the build runner as stuck and fail the test
BUILD_TIME_LIMIT: float = 330.0
# If minerals reach this amount the build is clearly not spending resources,
# so the build order has failed and the test should fail.
MINERAL_STUCK_THRESHOLD: float = 1000.0
# Only fail once minerals have stayed at/above the threshold for this long,
MINERAL_STUCK_DURATION: float = 15.0
# Log build progress every N game seconds so CI logs show where the build is at.
PROGRESS_LOG_INTERVAL: float = 30.0
# Wait this long after the build completes before verifying build order items,
VERIFICATION_DELAY: float = 12.0

# Structures whose `type_id` changes while they exist (lifted, lowered, rich
# or charged versions). Verification counts the whole family, so e.g. a
# lowered supply depot still satisfies a `SUPPLYDEPOT` requirement.
STRUCTURE_FAMILIES: dict[UnitTypeId, tuple[UnitTypeId, ...]] = {
    UnitTypeId.SUPPLYDEPOT: (
        UnitTypeId.SUPPLYDEPOT,
        UnitTypeId.SUPPLYDEPOTLOWERED,
    ),
    UnitTypeId.BARRACKS: (UnitTypeId.BARRACKS, UnitTypeId.BARRACKSFLYING),
    UnitTypeId.FACTORY: (UnitTypeId.FACTORY, UnitTypeId.FACTORYFLYING),
    UnitTypeId.STARPORT: (UnitTypeId.STARPORT, UnitTypeId.STARPORTFLYING),
    UnitTypeId.PYLON: (UnitTypeId.PYLON, UnitTypeId.PYLONOVERCHARGED),
    UnitTypeId.ASSIMILATOR: (
        UnitTypeId.ASSIMILATOR,
        UnitTypeId.ASSIMILATORRICH,
    ),
    UnitTypeId.EXTRACTOR: (UnitTypeId.EXTRACTOR, UnitTypeId.EXTRACTORRICH),
    UnitTypeId.REFINERY: (UnitTypeId.REFINERY, UnitTypeId.REFINERYRICH),
    UnitTypeId.GATEWAY: (UnitTypeId.GATEWAY, UnitTypeId.WARPGATE),
}

# terran units that transform into other unit types
UNIT_FAMILIES: dict[UnitTypeId, tuple[UnitTypeId, ...]] = {
    UnitTypeId.SIEGETANK: (UnitTypeId.SIEGETANK, UnitTypeId.SIEGETANKSIEGED),
    UnitTypeId.WIDOWMINE: (UnitTypeId.WIDOWMINE, UnitTypeId.WIDOWMINEBURROWED),
    UnitTypeId.HELLION: (UnitTypeId.HELLION, UnitTypeId.HELLIONTANK),
    UnitTypeId.LIBERATOR: (UnitTypeId.LIBERATOR, UnitTypeId.LIBERATORAG),
}

TOWNHALL_FAMILIES: dict[UnitTypeId, tuple[UnitTypeId, ...]] = {
    UnitTypeId.COMMANDCENTER: (
        UnitTypeId.COMMANDCENTER,
        UnitTypeId.COMMANDCENTERFLYING,
        UnitTypeId.ORBITALCOMMAND,
        UnitTypeId.ORBITALCOMMANDFLYING,
        UnitTypeId.PLANETARYFORTRESS,
    ),
    UnitTypeId.HATCHERY: (UnitTypeId.HATCHERY, UnitTypeId.LAIR, UnitTypeId.HIVE),
    UnitTypeId.NEXUS: (UnitTypeId.NEXUS,),
}

# Ability that morphs a structure into another structure, and the resulting
# structure type it produces.
ABILITY_TO_MORPH_RESULT: dict[AbilityId, UnitTypeId] = {
    AbilityId.UPGRADETOORBITAL_ORBITALCOMMAND: UnitTypeId.ORBITALCOMMAND,
    AbilityId.UPGRADETOLAIR_LAIR: UnitTypeId.LAIR,
    AbilityId.UPGRADETOHIVE_HIVE: UnitTypeId.HIVE,
    AbilityId.UPGRADETOPLANETARYFORTRESS_PLANETARYFORTRESS: (
        UnitTypeId.PLANETARYFORTRESS
    ),
}

# The result of a townhall morph is checked against its own family
MORPH_RESULT_FAMILIES: dict[UnitTypeId, tuple[UnitTypeId, ...]] = {
    UnitTypeId.ORBITALCOMMAND: (
        UnitTypeId.ORBITALCOMMAND,
        UnitTypeId.ORBITALCOMMANDFLYING,
    ),
    UnitTypeId.LAIR: (UnitTypeId.LAIR,),
    UnitTypeId.HIVE: (UnitTypeId.HIVE,),
    UnitTypeId.PLANETARYFORTRESS: (UnitTypeId.PLANETARYFORTRESS,),
}

# Addons can be swapped between production buildings (via `addonswap`), which
# changes their `type_id` (e.g. a reactor moved onto a factory becomes
# `FACTORYREACTOR`). Verification counts every addon of the same kind. The
# generic `REACTOR`/`TECHLAB` types cover addons still under construction.
ADDON_FAMILIES: dict[UnitTypeId, tuple[UnitTypeId, ...]] = {
    UnitTypeId.BARRACKSREACTOR: (
        UnitTypeId.REACTOR,
        UnitTypeId.BARRACKSREACTOR,
        UnitTypeId.FACTORYREACTOR,
        UnitTypeId.STARPORTREACTOR,
    ),
    UnitTypeId.BARRACKSTECHLAB: (
        UnitTypeId.TECHLAB,
        UnitTypeId.BARRACKSTECHLAB,
        UnitTypeId.FACTORYTECHLAB,
        UnitTypeId.STARPORTTECHLAB,
    ),
}


def _family_members(
    type_id: UnitTypeId,
    families: dict[UnitTypeId, tuple[UnitTypeId, ...]],
) -> tuple[UnitTypeId, ...]:
    """Return every type that counts towards `type_id` within `families`.

    If `type_id` is not part of any family it only counts towards itself.
    """
    for members in families.values():
        if type_id in members:
            return members
    return (type_id,)


class BuildRunnerBot(AresBot):
    """Run a single opening build from a configured builds file in one game.

    `main` restarts the game for every build, so each build is tested from a
    fresh start. Once the build completes the bot leaves the game and the
    next build is tested. If the build gets stuck the bot raises, which the
    test wrapper treats as a failure.
    """

    def __init__(self, build_to_test: str) -> None:
        super().__init__()
        self._build_to_test: str = build_to_test
        self._last_progress_log_time: float = 0.0
        self._mineral_warning_logged: bool = False
        self._mineral_stuck_since: float = 0.0
        self._verification_start_time: float = 0.0

    async def on_before_start(self) -> None:
        await super().on_before_start()
        with open(BUILDS_FILE) as config_file:
            build_config: dict = yaml.safe_load(config_file)
        # don't write data files during the test
        build_config["UseData"] = False
        self.config.update(build_config)

    async def on_start(self) -> None:
        await super().on_start()
        self.client.game_step = 8
        self.build_order_runner.switch_opening(self._build_to_test)
        logger.info(
            f"Build runner test - race: {BUILD_RUNNER_RACE.name}, "
            f"build: {self._build_to_test}"
        )

    async def on_step(self, iteration: int) -> None:
        await super().on_step(iteration)
        for depot in self.mediator.get_own_structures_dict[UnitTypeId.SUPPLYDEPOT]:
            depot(AbilityId.MORPH_SUPPLYDEPOT_LOWER)

        self.register_behavior(Mining())

        # periodically log progress so CI logs show where the build is at
        if self.time - self._last_progress_log_time >= PROGRESS_LOG_INTERVAL:
            self._last_progress_log_time = self.time
            logger.info(
                f"[{self._build_to_test}] step "
                f"{self.build_order_runner.build_step + 1}/"
                f"{len(self.build_order_runner.build_order)} | "
                f"time {self.time:.0f}s | "
                f"supply {self.supply_used}/{self.supply_cap} | "
                f"minerals {self.minerals:.0f}"
            )

        # warn once if minerals are rising towards the stuck threshold
        if (
            not self._mineral_warning_logged
            and self.minerals >= MINERAL_STUCK_THRESHOLD * 0.7
        ):
            self._mineral_warning_logged = True
            logger.warning(
                f"[{self._build_to_test}] minerals rising "
                f"({self.minerals:.0f}), build may be stuck"
            )

        # track how long minerals have been at/above the stuck threshold
        if self.minerals >= MINERAL_STUCK_THRESHOLD:
            if self._mineral_stuck_since == 0.0:
                self._mineral_stuck_since = self.time
        else:
            self._mineral_stuck_since = 0.0

        if self.build_order_runner.build_completed:
            if self._verification_start_time == 0.0:
                self._verification_start_time = self.time
                logger.info(
                    f"Build {self._build_to_test} completed - "
                    f"waiting {VERIFICATION_DELAY:.0f}s before "
                    f"verifying build order items"
                )
            if self.time - self._verification_start_time >= VERIFICATION_DELAY:
                missing: list[str] = self._verify_build_order()
                if not missing:
                    logger.info(f"Build {self._build_to_test} verified successfully")
                    await self.client.leave()
                else:
                    logger.error(
                        f"Build {self._build_to_test} verification failed, "
                        f"missing build order items: {missing}"
                    )
                    raise RuntimeError(
                        f"Build runner test failed: {self._build_to_test} "
                        f"completed but missing build order items: "
                        f"{', '.join(missing)}"
                    )
        elif (
            self._mineral_stuck_since > 0.0
            and self.time - self._mineral_stuck_since >= MINERAL_STUCK_DURATION
        ):
            logger.error(
                f"Build {self._build_to_test} failed: minerals have been at "
                f"{self.minerals:.0f} (>= {MINERAL_STUCK_THRESHOLD:.0f}) for "
                f"{self.time - self._mineral_stuck_since:.0f}s, "
                f"build order is not spending resources"
            )
            raise RuntimeError(
                f"Build runner test failed: {self._build_to_test} stuck with "
                f"{self.minerals:.0f} minerals at {self.time:.0f}s game time"
            )
        elif self.time > BUILD_TIME_LIMIT:
            logger.error(
                f"Build {self._build_to_test} did not complete within "
                f"{BUILD_TIME_LIMIT} seconds of game time"
            )
            raise RuntimeError(
                f"Build runner test failed: {self._build_to_test} did not complete"
            )

    def _verify_build_order(self) -> list[str]:
        """Check every verifiable item in the build order actually exists.

        Structures count as present if they exist or are under construction.
        Units (including workers) count as present if they exist or are still
        being trained. Upgrades count as present if complete or being
        researched. Townhall morphs (e.g. orbital) count as present if the
        resulting structure exists.

        Returns
        -------
        list[str] :
            Human readable descriptions of any missing build order items.
        """
        missing: list[str] = []
        required_structures: dict[UnitTypeId, int] = {}
        required_units: dict[UnitTypeId, int] = {}

        def _count_requirement(key: UnitTypeId) -> None:
            if key in ALL_STRUCTURES:
                required_structures[key] = required_structures.get(key, 0) + 1

            else:
                required_units[key] = required_units.get(key, 0) + 1

        for step in self.build_order_runner.build_order:
            command: AbilityId | UnitTypeId | UpgradeId = step.command
            if isinstance(command, UnitTypeId):
                _count_requirement(command)
            elif isinstance(command, AbilityId) and command in ABILITY_TO_MORPH_RESULT:
                # addon swaps just relocate an existing addon, and scouting /
                # cancelling commands leave no persistent artifact to check
                _count_requirement(ABILITY_TO_MORPH_RESULT[command])

        for structure_type, required in required_structures.items():
            present: int = self._present_structure_count(structure_type)
            if present < required:
                missing.append(
                    f"{structure_type.name} structure (need {required}, have {present})"
                )

        for unit_type, required in required_units.items():
            present: int = self._present_unit_count(unit_type)
            if present < required:
                missing.append(
                    f"{unit_type.name} unit (need {required}, have {present})"
                )

        for step in self.build_order_runner.build_order:
            if isinstance(
                step.command, UpgradeId
            ) and not self.pending_or_complete_upgrade(step.command):
                missing.append(f"{step.command.name} upgrade")

        return missing

    def _present_structure_count(self, structure_type: UnitTypeId) -> int:
        """Count how many structures count towards a `structure_type` requirement.

        Includes structures under construction and workers still travelling to
        build. Counts the whole family so e.g. a lowered supply depot satisfies
        a `SUPPLYDEPOT` requirement, and an Orbital Command satisfies a
        `COMMANDCENTER` requirement.
        """
        if structure_type in MORPH_RESULT_FAMILIES:
            # a townhall morph requirement only counts the resulting structure
            members: tuple[UnitTypeId, ...] = MORPH_RESULT_FAMILIES[structure_type]
        elif structure_type in TOWNHALL_FAMILIES:
            members = TOWNHALL_FAMILIES[structure_type]
        else:
            members = _family_members(
                structure_type, STRUCTURE_FAMILIES | ADDON_FAMILIES
            )

        present: int = 0
        for member in members:
            present += len(self.mediator.get_own_structures_dict[member])
            present += self.not_started_but_in_building_tracker(member)
        return present

    def _present_unit_count(self, unit_type: UnitTypeId) -> int:
        """Count how many units count towards a `unit_type` requirement.

        Includes units still being trained. Counts the whole family so e.g. a
        sieged Siege Tank satisfies a `SIEGETANK` requirement.
        """
        present: int = 0
        present += int(self.already_pending(unit_type))
        for member in _family_members(unit_type, UNIT_FAMILIES):
            present += len(self.mediator.get_own_army_dict[member])
        return present


# Start game
if __name__ == "__main__":
    # GitHub Actions friendly logging: plain text to stdout so CI logs are
    # easy to read and `travis_test_script.py` captures bot output
    logger.remove()
    logger.add(
        sys.stdout,
        level="INFO",
        colorize=False,
        format="[{time:HH:mm:ss} | {level: <8}] {message}",
    )

    logger.info(
        f"Build runner config - race: {BUILD_RUNNER_RACE.name}, file: {BUILDS_FILE}"
    )

    with open(BUILDS_FILE) as config_file:
        builds_config: dict = yaml.safe_load(config_file)
    builds_to_run: list[str] = list(builds_config[BUILDS].keys())

    random_maps: list[str] = [
        "IncorporealAIE_v4",
        "PersephoneAIE_v4",
        "PylonAIE_v4",
        "TorchesAIE_v4",
    ]

    failed_builds: list[tuple[str, Exception]] = []
    for build_name in builds_to_run:
        map_name: str = random.choice(random_maps)
        logger.info(f"Starting new game to test build: {build_name} (map: {map_name})")
        try:
            run_game(
                maps.get(map_name),
                [
                    Bot(
                        BUILD_RUNNER_RACE,
                        BuildRunnerBot(build_name),
                        "BuildRunnerBot",
                    ),
                    Computer(Race.Random, Difficulty.VeryEasy),
                ],
                realtime=False,
            )
            logger.info(f"Build '{build_name}' passed")
        except Exception as e:
            failed_builds.append((build_name, e))
            logger.exception(f"Build '{build_name}' failed: {e}")

    if failed_builds:
        logger.error("Build runner test FAILED")
        for build_name, err in failed_builds:
            logger.error(f"  - {build_name}: {err}")
        raise SystemExit(1)

    logger.info("All build runner tests passed")
