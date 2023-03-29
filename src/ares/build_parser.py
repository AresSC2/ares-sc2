from dataclasses import dataclass
from os import path

import yaml
from sc2.data import Race

from src.ares.consts import CONFIG_FILE

# from ares import AresBot


@dataclass
class BuildParser:
    """Process user build order yaml files.

    If no builds.yml files are present use a default bot mode

    Attributes
    ----------
    config : dict
        Already parsed config.yml file as a dict.
    user_build_file_location : str
        Path to user builds.yml file.
    """

    race: Race
    config: dict

    def parse(self) -> list[str]:
        """
        Handle internal and user config

        Returns
        -------
        Dict :
            Internal parsed config.yml by default, or the merged internal and
            users config files.
        """
        print(self._builds_file_name())

    def _builds_file_name(self) -> str:
        """
        Depending on user's race, get the file name to search for.

        Returns
        -------
        str : name of yaml file we should parse.
        """
        return f"{self.race.name.lower()}_builds.yml"
