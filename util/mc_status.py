import asyncio
import threading

from mcstatus import MinecraftServer as mc, MinecraftBedrockServer as mcb

JAVA = 1
BE = 2

# https://github.com/py-mine/mcstatus
# JavaEdition default port:25565
# BedrockEdition default port:19132


class minecraft_status:
    """Minecraft server status"""

    def error_check(arg):
        """エラーの種類がネットワーク系のエラーかどうかを調べます。"""
        return type(arg) == ConnectionRefusedError or type(arg) == OSError

    async def java_unsync(loop, address):
        return await loop.run_in_executor(
            None, minecraft_status.java, address
        )

    async def bedrock_unsync(loop, address):
        return await loop.run_in_executor(
            None, minecraft_status.bedrock, address
        )

    def java(address):
        """Minecraft:Java Edition"""
        try:
            server = mc.lookup(address)
            status = server.status()
            return status
        except BaseException as err:
            return err

    def bedrock(address):
        """Minecraft:Bedrock Edition"""
        try:
            server = mcb.lookup(address)
            status = server.status()
            return status
        except BaseException as err:
            return err
