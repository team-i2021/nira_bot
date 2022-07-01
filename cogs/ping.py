import asyncio
import ipaddress
import json
import logging
import os
import platform
import subprocess
import sys
import traceback
from subprocess import PIPE

import HTTP_db
import nextcord
from nextcord import Interaction, SlashOption, ChannelType
from nextcord.ext import commands

from util import admin_check, n_fc, eh, database

# pingを送信するだけ

DISCORD = 0xD13C06D

SYSDIR = sys.path[0]


async def ping_there(adr, message: nextcord.Message or Interaction):
    command = ""
    if platform.system() == "Windows":
        command = f"ping {adr} -n 3 -w 3"
    elif platform.system() == "Linux":
        command = f"ping {adr} -c 3 -W 3"
    elif platform.system() == "Darwin":
        command = f"ping {adr} -c 3 -t 3"
    else:
        print(
            f"Unsupported OS: {platform.system()}\nPing command may not work.")
        command = f"ping {adr} -c 3 -W 3"
    res = subprocess.run(
        command,
        stdout=PIPE,
        stderr=PIPE,
        shell=True,
        text=True
    )
    if res.returncode == 0:
        await message.edit(embed=nextcord.Embed(title="Ping", description=f"`{adr}`に時間内に接続できました。\n```sh\n{res.stdout}```", color=0x00ff00))
    else:
        await message.edit(embed=nextcord.Embed(title="Ping", description=f"`{adr}`に時間内に接続できませんでした。", color=0x00ff00))

# ctx.message == None:こまんど


async def base_ping(bot, client: HTTP_db.Client, adr, message: nextcord.Message or Interaction):
    if adr == DISCORD:
        bot_latency = round(bot.latency * 1000, 3)
        await message.edit(embed=nextcord.Embed(title="Ping", description=f"- Discord Server```\n{bot_latency}ms```\n- Database Server```\nConnecting...```", color=0x00ff00))
        try:
            data = await client.ping()
            db_latency = round(float(data.ping) * 1000, 3)
            await message.edit(embed=nextcord.Embed(title="Ping", description=f"- Discord Server```\n{bot_latency}ms```\n- Database Server```\n{db_latency}ms```", color=0x00ff00))
            return
        except Exception as err:
            await message.edit(embed=nextcord.Embed(title="Ping", description=f"- Discord Server```\n{bot_latency}ms```\n- Database Server```\nDatabase Connection Error.\n{err}```", color=0x00ff00))
            return

    elif adr != DISCORD:
        try:
            if adr == "localhost" or ipaddress.ip_address(adr).is_private:
                await message.edit(embed=nextcord.Embed(title="Ping", description=f"`localhost`及びLAN内へのPingはできません。", color=0x00ff00))
                return
        except Exception:
            pass
        try:
            await asyncio.wait_for(ping_there(adr, message), timeout=8)
            return
        except BaseException as err:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            logging.error(
                f"大変申し訳ございません。エラーが発生しました。\n```{err}```\n```sh\n{sys.exc_info()}```\nfile:`{fname}`\nline:{exc_tb.tb_lineno}")
            await message.edit(embed=nextcord.Embed(title="Ping", description=f"内部エラーが発生しました。\n```py\n{traceback.format_exc()}```", color=0xff0000))
        return


class Ping(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        datas = json.load(open(f'{SYSDIR}/setting.json', 'r'))["database_data"]
        self.client = database.openClient()

    @nextcord.slash_command(name="ping", description="Discordサーバー又は、指定サーバーとのレイテンシを計測します。", guild_ids=n_fc.GUILD_IDS)
    async def ping_slash(
        self,
        interaction: Interaction,
        address: str = SlashOption(
            name="address",
            description="アドレス。指定しないとDiscordサーバーとのRTTを表示します。",
            required=False,
        )
    ):
        if address is None:
            address = DISCORD
        await interaction.send(embed=nextcord.Embed(title="Ping", description=f"Ping測定中...", color=0x00ff00))
        await base_ping(self.bot, self.client, address, await interaction.original_message())

    @commands.command(name="ping", help="""\
レイテンシを表示します。
`n!ping`で、DiscordサーバーとBOTサーバーとのレイテンシを表示します。
`n!ping [address]`という風に、アドレスを指定すると、そのアドレスとのpingを測定します。
ローカルIP及びlocalhostにはping出来ません。多分....。
また、pingは実測値ですが、当然参考値にしてください。

引数1:address(str)
IPアドレスまたはドメインの形で指定してください。""")
    async def ping(self, ctx: commands.Context):
        message = await ctx.reply(embed=nextcord.Embed(title="Ping", description=f"Ping測定中...", color=0x00ff00))
        texts = ctx.message.content.split(" ", 1)
        if len(texts) == 1:
            await base_ping(self.bot, self.client, DISCORD, message)
        else:
            await base_ping(self.bot, self.client, texts[1], message)


def setup(bot):
    bot.add_cog(Ping(bot))
