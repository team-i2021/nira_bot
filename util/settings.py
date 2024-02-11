import sys
from typing import Any, Annotated

from pydantic import BeforeValidator, Field, NonNegativeInt, PositiveInt, SecretStr
from pydantic.networks import UrlConstraints
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource

from util.typing import LoggerLevel

NonEmptyStr = Annotated[str, Field(min_length=1)]
NonEmptySecretStr = Annotated[SecretStr, Field(min_length=1)]
MongoSRVDsn = Annotated[MultiHostUrl, UrlConstraints(allowed_schemes=["mongodb+srv"])]


class SettingsBase(BaseSettings):
    model_config = {
        "extra": "ignore",
        "frozen": True,
    }

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return env_settings, dotenv_settings, file_secret_settings, init_settings


class Tokens(SettingsBase):
    nira_bot: Annotated[SecretStr, Field(min_length=1)]


def _upper_level(level: Any) -> Any:
    return level.upper() if isinstance(level, str) else level


class Logging(SettingsBase):
    filepath: NonEmptyStr = f"{sys.path[0]}/nira.log"
    format: str = "%(asctime)s$%(filename)s$%(lineno)d$%(funcName)s$%(levelname)s:%(message)s"
    level: Annotated[int | LoggerLevel, BeforeValidator(_upper_level)] = "INFO"


class BotSettings(SettingsBase):
    # トークンとか (必須)
    tokens: Tokens

    # API キー
    translate: NonEmptyStr | None = None
    voicevox: tuple[NonEmptyStr, ...] = ()
    talk_api: NonEmptyStr | None = None
    gcloud_api: NonEmptyStr | None = None

    # データベース周り
    database_url: MongoSRVDsn
    database_name: NonEmptyStr = "nira-bot"

    # Bot の起動に必要だがデフォルト値を提供できるもの
    prefix: str = "n!"
    shard_id: NonNegativeInt = 0
    shard_count: PositiveInt = 1
    logging: Logging = Logging()

    # 上同だが任意のもの
    py_admin: tuple[NonNegativeInt, ...] = ()
    guild_ids: tuple[NonNegativeInt, ...] = ()

    # デバッグ用: Cog
    unload_cogs: tuple[NonEmptyStr, ...] = ()
    load_cogs: tuple[NonEmptyStr, ...] = ()
