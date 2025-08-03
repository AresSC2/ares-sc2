import sys
from dataclasses import dataclass
from os import path

import yaml


@dataclass
class ConfigParser:
    """Process user and internal config.

    Internal config is used by default, optional user config overrides default values

    Attributes
    ----------
    ares_config_location : str
        Path to internal Ares config.yml file.
    user_config_location : str
        Path to user config.yml file.
    """

    ares_config_location: str
    user_config_location: str
    config_file_name: str

    def parse(self) -> dict:
        """
        Handle internal and user config

        Returns
        -------
        Dict :
            Internal parsed config.yml by default, or the merged internal and
            users config files.
        """
        internal_config_path: str = path.join(
            self.ares_config_location, self.config_file_name
        )
        user_config_path: str = path.join(
            self.user_config_location, self.config_file_name
        )
        if path.isfile(internal_config_path):
            with open(internal_config_path, "r") as config_file:
                internal_config: dict = yaml.safe_load(config_file)
        else:
            raise Exception("Internal Ares config.yml file is missing")

        if path.isfile(user_config_path):
            with open(user_config_path, "r") as config_file:
                user_config: dict = yaml.safe_load(config_file)
        # if no user config, fine to return internal_config here
        else:
            return internal_config

        # there is a user config and internal config, sort out the differences
        return self._merge_config_files(internal_config, user_config)

    def get_resource_path(self, relative_path: str) -> str:
        """Get absolute path to resource, works for dev and for PyInstaller"""
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = path.abspath(".")

        return path.join(base_path, relative_path)

    def _merge_config_files(self, internal_config: dict, user_config: dict) -> dict:
        """
        Merge internal and user config files so we are left with just one.

        Start off with the internal_config, then override any matching keys
        in the user_config. Types the user pass in need to be checked.

        Parameters
        ----------
        internal_config :
            Internal config dictionary already parsed from the original yaml file.
        user_config :
            User config dictionary already parsed from the original yaml file.

        Returns
        -------
        Dict :
            A single config dictionary where user values override default values.
        """
        """Recursively merge override dictionary into default dictionary."""
        for key, value in user_config.items():
            if (
                isinstance(value, dict)
                and key in internal_config
                and isinstance(internal_config[key], dict)
            ):
                # Recursively merge dictionaries
                internal_config[key] = self._merge_config_files(
                    internal_config[key], value
                )
            else:
                # Override or add the value
                internal_config[key] = value
        return internal_config
