""" Settings management (API url, config file, path, API version...) """
import json
from pathlib import Path

from click.utils import get_app_dir
from pydantic import BaseSettings, Field

from inferex import __app_name__
from inferex.sdk.logs import get_logger


logger = get_logger(__name__)

class ClientSettings(BaseSettings):
    """ Settings class, inherits from pydantic BaseSettings. """

    config_path: Path = Field(default=Path(get_app_dir(__app_name__)) / "config.json")
    api_token: str = Field(default="", env='INFEREX_TOKEN')
    base_url: str = Field(default="https://api.inferex.com", env="INFEREX_API")
    api_vers: str = Field(default="", env="INFEREX_API_VERSION")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.api_token = self.api_token or self.read_config().get('access_token')  # prefer env variable to config file

    def write_token(self, token) -> None:
        """ Write token to the filesystem and update. """
        data = self.read_config() if self.config_path.exists() else {}
        data['access_token'] = token
        with open(self.config_path, "w", encoding=self.__config__.env_file_encoding) as json_file:
            json.dump(data, json_file)
        self.api_token = token
        logger.info(f"Token written to {self.config_path}")

    def read_config(self) -> dict:
        """ Read the user's config file from the filesystem. """
        data = None
        try:
            with open(self.config_path, "r", encoding=self.__config__.env_file_encoding) as file:
                data = json.load(file)
        except (json.JSONDecodeError, FileNotFoundError) as exc:
            logger.info(exc)

        if data:
            logger.info(f"Config read from {self.config_path}")

        return data or {}

    def delete_config(self) -> Path:
        """ Removes the inferex config.json file as well as the app folder. """
        if not self.config_path.is_file():
            return 1

        self.config_path.unlink()
        logger.info(f"Removed {self.config_path}")
        self.config_path.parent.rmdir()
        logger.info(f"Removed {self.config_path.parent}")
        return self.config_path

    @property
    def url(self):
        """ Return a versioned API url string. """
        return self.base_url + self.api_vers


settings = ClientSettings()
