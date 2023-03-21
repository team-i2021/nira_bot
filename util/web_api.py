import logging
import os
import sys

import aiohttp

import nextcord
from nextcord.embeds import Embed

NOTIFY_URL = 'https://notify-api.line.me/api/notify'
TOKEN_CHECK = 'https://notify-api.line.me/api/status'

server_req_url = 'http://api.steampowered.com/ISteamApps/GetServersAtAddress/v1/?format=json&addr='

image_4 = [".jpg", ".png", ".bmp"]
image_5 = [".jpeg", ".jtif"]


async def notify_line(session: aiohttp.ClientSession, message: nextcord.Message, token: str) -> None:
    channel = f"[{message.guild.name}]/[{message.channel.name}]"
    try:
        if message.author.nick == None:
            user = f"{message.author.name}@{message.author.discriminator}"
        else:
            user = f"{message.author.nick}"
    except Exception:
        user = f"{message.author.name}@{message.author.discriminator}"
    try:
        if message.author.bot:
            user = user + "[BOT]"
        if message.attachments != [] or ((message.content[:8] == "https://" or message.content[:7] == "http://") and (message.content[-5:] == ".jpeg" or message.content[-4:] == ".jpg" or message.content[-4:] == ".png")):
            if message.attachments == []:
                image = message.content
            elif message.attachments[0].url[-5:] == ".jpeg" or message.attachments[0].url[-4:] == ".jpg" or message.attachments[0].url[-4:] == ".png":
                image = message.attachments[0].url
        else:
            image = ""
        if message.embeds != [] and message.embeds[0].title != Embed.Empty:
            embed = f"{message.embeds[0].title}\n{message.embeds[0].description}"
        else:
            embed = ""
        mes = f"\n{channel}\n{user}\n{message.content}\n{embed}"
        if len(mes) > 1000:
            over = len(mes) - 1000
            mes = f"\n{channel}\n{user}\n{message.content[-over:]}...\n{embed}\n※本文が長いため省略されました。"
        # mes = f"\n[{message.guild.name}]/[{message.channel.name}]\n{message.author.nick}\n\n{message.content}"
        headers = {'Authorization' : 'Bearer ' + token}
        if image == "":
            payload = {'message' : mes}
        else:
            payload = {'message' : mes, 'imageFullsize' : image, 'imageThumbnail': image}
        # print(payload)
        await session.post(NOTIFY_URL, headers=headers, data=payload)
    except Exception as err:
        _, _, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        logging.warn(f"大変申し訳ございません。エラーが発生しました。\n```{err}```\n```sh\n{sys.exc_info()}```\nfile:`{fname}`\nline:{exc_tb.tb_lineno}")


async def line_token_check(session: aiohttp.ClientSession,token: str) -> tuple[bool, str]:
    headers = {'Authorization' : 'Bearer ' + token}
    async with session.get(TOKEN_CHECK, headers=headers) as response:
        if response.status == 200:
            return (True, await response.text())
        else:
            return (False, await response.text())
