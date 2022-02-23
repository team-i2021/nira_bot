from mcstatus import MinecraftServer as mc, MinecraftBedrockServer as mcb
import asyncio
import threading
from timeout_decorator import timeout, TimeoutError

JAVA = 1
BE = 2

# https://github.com/py-mine/mcstatus
# JavaEdition default port:25565
# BedrockEdition default port:19132



class minecraft:
    """Minecraft server status"""

    def error_handle(arg):
        return type(arg) == TimeoutError or type(arg) == ConnectionRefusedError or type(arg) == OSError

    async def identify(host, port):
        java_check = threading.Thread(target=minecraft.java, args=(host, port))
        be_check = threading.Thread(target=minecraft.bedrock, args=(host, port))
        java_response = java_check.start()
        be_response = be_check.start()
        await asyncio.sleep(4)
        j, b = (True, True)
        if minecraft.error_handle(java_response):
            j = False
        if minecraft.error_handle(be_response):
            b = False


    @timeout(3)
    def java(host, port):
        """Minecraft:Java Edition"""
        try:
            address = f"{host}:{port}"
            server = mc.lookup(address)
            status = server.status()
            return status
        except BaseException as err:
            return err


    @timeout(3)
    async def bedrock(host, port):
        """Minecraft:Bedrock Edition(統合版)"""
        try:
            address = f"{host}:{port}"
            server = mcb.lookup(address)
            status = server.status()
            return status
        except BaseException as err:
            return err