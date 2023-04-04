from pydantic import BaseSettings, Extra, Field, MongoDsn, PositiveInt, SecretStr
from pydantic.env_settings import SettingsSourceCallable


class MongoDsnWithSrv(MongoDsn):
    allowed_schemes = {"mongodb", "mongodb+srv"}


class SettingsBase(BaseSettings):
    class Config:
        @classmethod
        def customize_sources(
            cls,
            init_settings: SettingsSourceCallable,
            env_settings: SettingsSourceCallable,
            file_secret_settings: SettingsSourceCallable,
        ) -> tuple[SettingsSourceCallable, ...]:
            return env_settings, init_settings, file_secret_settings

        extra = Extra.ignore
        frozen = True


class Tokens(SettingsBase):
    nira_bot: SecretStr = Field(min_length=1, env="BOT_TOKEN")


class BotSettings(SettingsBase):
    # トークンとか (必須)
    tokens: Tokens

    # API キー
    translate: str | None = Field(default=None, min_length=1)
    voicevox: tuple[str, ...] = ()

    # データベース周り
    database_url: MongoDsnWithSrv
    database_name: str = Field(default="nira-bot", min_length=1)

    # Bot の起動に必要だがデフォルト値を提供できるもの
    prefix: str = "n!"
    shard_id: int = Field(default=0, ge=0)
    shard_count: PositiveInt = 1

    # 上同だが任意のもの
    py_admin: tuple[int, ...] = ()
    guild_ids: tuple[int, ...] = ()

    # デバッグ用: Cog
    unload_cogs: tuple[str, ...] = ()
    load_cogs: tuple[str, ...] = ()

    # hoyo.py: HoYoverse 通行証のログインに使用するトークンと ID
    ltuid: int | None = None  # 見ようと思えば他人から見れる...はず
    ltoken: SecretStr | None = Field(default=None, min_length=1)  # 絶対アカン (private)
