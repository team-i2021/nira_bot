import nextcord
from nextcord.ext import commands

import HTTP_db

from util.n_fc import py_admin

class NIRA(commands.Bot):
    """I AM NIRA BOT!!!"""
    def __init__(self, debug: bool = False, token: str = None, client: HTTP_db.Client = None, *args, **kwargs):
        self.debug: bool = debug
        self._token: str = token
        self.client: HTTP_db.Client = client
        #self.main_prefix: str = (lambda x: x[0] if type(x) in [list, tuple, set] else x)(**kwargs[""])
        return super().__init__(*args, **kwargs)

    def run(self) -> None:
        super().run(self._token, reconnect=True)

    async def is_owner(self, user: nextcord.User) -> bool:
        if user.id in py_admin:
            return True
        else:
            return await super().is_owner(user)
    
    class Forbidden(Exception):
        pass

    class ForbiddenExpand(Exception):
        pass
