import nextcord
from nextcord.ext import commands

import motor
from motor import motor_asyncio

from util.n_fc import py_admin

class NIRA(commands.Bot):
    """
    I AM NIRA BOT!!!
    
    An object that extends `commands.Bot`.
    """
    def __init__(
            self,
            debug: bool = False,
            token: str = None,
            client = None,
            mongo: motor.motor_asyncio.AsyncIOMotorClient = None,
            database_name: str = "nira-bot"
            *args,
            **kwargs
        ):
        self.debug: bool = debug
        self.__token: str = token
        self.client = client # HTTP_dbとして呼び出す（今まで通りself.client + database.default_pushとかで呼び出す）

        self.__mongo: motor_asyncio.AsyncIOMotorClient = mongo # おいてるだけだから使わない

        self.database: motor_asyncio.AsyncIOMotorDatabase = self.__mongo[database_name] # MongoDBとして呼び出す（self.database["collection_name"]として呼び出す）
        self.database_name: str = database_name

        self.ready_shard = []
        #self.main_prefix: str = (lambda x: x[0] if type(x) in [list, tuple, set] else x)(**kwargs[""])
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
