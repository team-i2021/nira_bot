import asyncio
import threading
import mcstatus

from mcstatus import JavaServer, BedrockServer

JAVA = 1
BE = 2

# https://github.com/py-mine/mcstatus
# JavaEdition default port:25565
# BedrockEdition default port:19132

async def java_status(host: str, port: int) -> mcstatus.pinger.PingResponse:
    """Status checker of JAVA"""
    try:
        server = JavaServer(host=host, port=port)
        status = await server.async_status()
        return status
    except Exception as err:
        return err

async def bedrock_status(host: str, port: int) -> mcstatus.bedrock_status.BedrockStatusResponse:
    """Status checker of BEDROCK"""
    try:
        server = BedrockServer(host=host, port=port)
        status = await server.async_status()
        return status
    except Exception as err:
        return err
