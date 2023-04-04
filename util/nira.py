import aiohttp

import nextcord
from HTTP_db import Client
from motor.motor_asyncio import AsyncIOMotorClient
from nextcord.ext import commands

from util.n_fc import py_admin

from typing import Any


class NIRA(commands.Bot):
    """
    I AM NIRA BOT!!!

    An object that extends `commands.Bot`.
    """

    def __init__(
        self,
        client: Client,
        mongo: AsyncIOMotorClient,
        debug: bool = False,
        token: str | None = None,
        database_name: str = "nira-bot",
        shard_id: int = 0,
        shard_count: int = 1,
        settings: dict[str, dict[str, str] | list[str | int] | str | int] | None = None,
        *args: Any,
        **kwargs: Any,
    ):
        self.debug = debug
        self.__token = token
        self.client = client  # HTTP_dbとして呼び出す（今まで通りself.client + database.default_pushとかで呼び出す）

        self.__mongo = mongo  # おいてるだけだから使わない

        # MongoDBとして呼び出す（self.database["collection_name"]として呼び出す）
        self.database = self.__mongo[database_name]
        self.database_name = database_name

        self.shard_id = shard_id
        self.shard_count = shard_count
        self.settings = settings

        self.session = aiohttp.ClientSession()
        # self.main_prefix: str = (lambda x: x[0] if type(x) in [list, tuple, set] else x)(**kwargs[""])
        return super().__init__(*args, **kwargs)

    def run(self) -> None:
        super().run(self.__token, reconnect=True)

    async def is_owner(self, user: nextcord.User) -> bool:
        if user.id in py_admin:
            return True
        else:
            return await super().is_owner(user)

    class Forbidden(Exception):
        """Exception of default Forbidden (not Server Admin)"""

    class ForbiddenExpand(Exception):
        """Exception of expanded Forbidden (not Bot Admin)"""
