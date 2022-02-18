from mcstatus import MinecraftServer as mc, MinecraftBedrockServer as mcb

# https://github.com/py-mine/mcstatus
# JavaEdition default port:25565
# BedrockEdition default port:19132

class minecraft:
    """Minecraft server status"""
    def java(host, port):
        """Minecraft:Java Edition"""
        try:
            
            address = f"{host}:{port}"
            server = mc.lookup(address)
            status = server.status()
            return status
        except BaseException as err:
            return str(err)
    
    def bedrock(host, port):
        """Minecraft:Bedrock Edition(統合版)"""
        try:
            address = f"{host}:{port}"
            server = mcb.lookup(address)
            status = server.status()
            return status
        except BaseException as err:
            return str(err)