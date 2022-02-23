from mcstatus import MinecraftServer as mc, MinecraftBedrockServer as mcb
import asyncio
import threading
from timeout_decorator import timeout, TimeoutError

JAVA = 1
BE = 2

# https://github.com/py-mine/mcstatus
# JavaEdition default port:25565
# BedrockEdition default port:19132



class minecraft_status:
    """Minecraft server status"""

    def error_check(arg):
        """エラーの種類がネットワーク系のエラーかどうかを調べます。"""
        return type(arg) == TimeoutError or type(arg) == ConnectionRefusedError or type(arg) == OSError

    @timeout(3, use_signals=False)
    async def java(host, port):
        """Minecraft:Java Edition"""
        try:
            loop = asyncio.get_event_loop()
            address = f"{host}:{port}"
            server = await loop.run_in_executor(None, mc.lookup, address)
            status = server.status()
            return status
        except BaseException as err:
            return err

    @timeout(3, use_signals=False)
    async def bedrock(host, port):
        """Minecraft:Bedrock Edition"""
        try:
            loop = asyncio.get_event_loop()
            address = f"{host}:{port}"
            server = await loop.run_in_executor(None, mcb.lookup, address)
            status = server.status()
            return status
        except BaseException as err:
            return err