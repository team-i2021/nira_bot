from typing import Any

import aiohttp
import nextcord
from motor.motor_asyncio import AsyncIOMotorClient
from nextcord.ext import commands

from util.n_fc import py_admin
from util.typing import GeneralChannel
from util.colors import Color

class NIRA(commands.Bot):
    """
    I AM NIRA BOT!!!

    An object that extends `commands.Bot`.
    """

    def __init__(
        self,
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

        self.__mongo = mongo  # おいてるだけだから使わない

        # MongoDBとして呼び出す（self.database["collection_name"]として呼び出す）
        self.database = self.__mongo[database_name]
        self.database_name = database_name

        self.shard_id = shard_id
        self.shard_count = shard_count
        self.settings = settings

        self.color = Color

        self._session = aiohttp.ClientSession()
        # self.main_prefix: str = (lambda x: x[0] if type(x) in [list, tuple, set] else x)(**kwargs[""])
        return super().__init__(*args, **kwargs)

    @property
    def session(self) -> aiohttp.ClientSession:
        if self._session.closed:
            self._session = aiohttp.ClientSession(loop=self.loop)
        return self._session

    def run(self) -> None:
        super().run(self.__token, reconnect=True)

    async def is_owner(self, user: nextcord.User) -> bool:
        if user.id in py_admin:
            return True
        else:
            return await super().is_owner(user)

    async def resolve_user(self, user_id: int) -> nextcord.User:
        user = self.get_user(user_id)
        if user is None:
            user = await self.fetch_user(user_id)
        return user

    async def resolve_guild(self, guild_id: int) -> nextcord.Guild:
        guild = self.get_guild(guild_id)
        if guild is None:
            guild = await self.fetch_guild(guild_id)
        return guild

    async def resolve_channel(self, channel_id: int) -> GeneralChannel:
        channel = self.get_channel(channel_id)
        if channel is None or isinstance(channel, nextcord.PartialMessageable):
            channel = await self.fetch_channel(channel_id)
        return channel

    class Forbidden(Exception):
        """Exception of default Forbidden (not Server Admin)"""

    class ForbiddenExpand(Exception):
        """Exception of expanded Forbidden (not Bot Admin)"""
