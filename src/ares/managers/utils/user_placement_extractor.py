from typing import TYPE_CHECKING

from sc2.data import Race

from ares.consts import BuildingPlacementOptions

if TYPE_CHECKING:
    from ares import AresBot


class UserPlacementExtractor:
    """Handles extraction and parsing of user-defined building placements from YAML."""

    def __init__(self, ai: "AresBot", user_placements: dict):
        self.ai = ai
        self.user_placements = user_placements

    @staticmethod
    def normalize_map_name(map_name: str) -> str:
        """Normalize map names so YAML keys don't need to match exactly."""
        map_name = map_name.lower()
        suffixes = ["le", "aie"]

        for suffix in suffixes:
            if map_name.endswith(suffix):
                map_name = map_name[: -len(suffix)]
            elif map_name.endswith(f" {suffix}"):
                map_name = map_name[: -len(suffix) - 1]

        return map_name.replace(" ", "")

    @staticmethod
    def iter_point_pairs(value: list) -> list[list[float]]:
        """
        Accepts any of:
          - [x, y]
          - [[x, y], [x, y], ...]
          - [[[x, y], ...], [[x, y]], ...]
          - mixtures of the above
        Returns a flat list of [x, y] pairs.
        """

        def _is_point_pair(v: list | tuple) -> bool:
            return (
                isinstance(v, (list, tuple))
                and len(v) == 2
                and all(isinstance(n, (int, float)) for n in v)
            )

        if value is None:
            return []

        if _is_point_pair(value):
            return [list(value)]

        if not isinstance(value, list):
            return []

        out: list[list[float]] = []
        stack: list = [value]
        while stack:
            cur = stack.pop()
            if _is_point_pair(cur):
                out.append([float(cur[0]), float(cur[1])])
            elif isinstance(cur, list):
                for item in reversed(cur):
                    stack.append(item)
        return out

    @staticmethod
    def race_to_key(enemy_race: Race) -> str:
        """Convert enemy race to YAML key format."""
        if enemy_race == Race.Zerg:
            return "VsZerg"
        elif enemy_race == Race.Protoss:
            return "VsProtoss"
        elif enemy_race == Race.Terran:
            return "VsTerran"
        else:
            return "VsRandom"

    @staticmethod
    def merge_defaults_no_override(
        *,
        defaults: dict | None,
        race_specific: dict | None,
    ) -> dict:
        """
        Merge two dicts where:
          - race_specific wins on key conflicts (defaults must not override)
          - if both values are lists, defaults are appended (deduped)
        """
        merged: dict = {}
        defaults = defaults or {}
        race_specific = race_specific or {}

        for k, v in race_specific.items():
            merged[k] = v

        for k, default_v in defaults.items():
            if k not in merged:
                merged[k] = default_v
                continue

            race_v = merged[k]
            if isinstance(race_v, list) and isinstance(default_v, list):
                merged[k] = race_v + [d for d in default_v if d not in race_v]

        return merged

    def get_spawn_block_for_current_game(self, spawn_loc: dict) -> dict | None:
        """Pick the correct spawn block (Upper/Lower) for the current game."""
        upper_spawn: bool = (
            self.ai.start_location.y > self.ai.enemy_start_locations[0].y
        )

        for spawn_key, block in spawn_loc.items():
            if upper_spawn and spawn_key == BuildingPlacementOptions.UPPER_SPAWN.value:
                return block
            if (
                not upper_spawn
                and spawn_key == BuildingPlacementOptions.LOWER_SPAWN.value
            ):
                return block

        return None

    def extract_placements_for_current_map(self) -> dict | None:
        """Get the building placement data for the current map if it exists."""
        current_map_norm = self.normalize_map_name(self.ai.game_info.map_name)

        for map_name, spawn_loc in self.user_placements.items():
            if self.normalize_map_name(map_name) != current_map_norm:
                continue

            building_location_info = self.get_spawn_block_for_current_game(spawn_loc)
            if not building_location_info:
                continue

            enemy_race: Race = self.ai.enemy_race
            race_key: str = self.race_to_key(enemy_race)

            return self.merge_defaults_no_override(
                defaults=building_location_info.get(
                    BuildingPlacementOptions.VS_ALL.value
                ),
                race_specific=building_location_info.get(race_key)
                if race_key
                else None,
            )

        return None
