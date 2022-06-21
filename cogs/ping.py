import logging
from util import admin_check, n_fc, eh
import asyncio
from nextcord.ext import commands
import nextcord
import subprocess
import traceback
from subprocess import PIPE
import os
import sys
from nextcord import Interaction, SlashOption, ChannelType
import json
import HTTP_db
import platform

sys.path.append('../')
# pingを送信するだけ

DISCORD = 0xD13C06D

# loggingの設定
dir = sys.path[0]


class NoTokenLogFilter(logging.Filter):
    def filter(self, record):
        message = record.getMessage()
        return 'token' not in message


logger = logging.getLogger(__name__)
logger.addFilter(NoTokenLogFilter())
formatter = '%(asctime)s$%(filename)s$%(lineno)d$%(funcName)s$%(levelname)s:%(message)s'
logging.basicConfig(
    format=formatter, filename=f'{dir}/nira.log', level=logging.INFO)


async def ping_there(adr, message: nextcord.Message or Interaction):
    command = ""
    if platform.system() == "Windows":
        command = f"ping {adr} -n 3 -w 3"
    elif platform.system() == "Linux":
        command = f"ping {adr} -c 3 -W 3"
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
        bot_latency = round(bot.latency * 1000, 2)
        await message.edit(embed=nextcord.Embed(title="Ping", description=f"- Discord Server\n`{bot_latency}`ms\n\n- Database Server\n`Connecting...`", color=0x00ff00))
        try:
            data = await client.ping()
            db_latency = round(float(data.ping), 2)
            await message.edit(embed=nextcord.Embed(title="Ping", description=f"- Discord Server\n`{bot_latency}`ms\n\n- Database Server\n`{db_latency}`ms", color=0x00ff00))
            return
        except HTTP_db.UnknownDatabaseError:
            await message.edit(embed=nextcord.Embed(title="Ping", description=f"- Discord Server\n`{bot_latency}`ms\n\n- Database Server\n`Connection Error.`", color=0x00ff00))
            return

    elif adr != DISCORD:
        if adr[8:] == "192.168." or adr == "127.0.0.1" or adr == "localhost" or adr == "0.0.0.0" or adr == "127.0.1" or adr == "127.1" or adr == "2130706433" or adr == "0x7F000001" or adr == "017700000001":
            await message.edit(embed=nextcord.Embed(title="Ping", description=f"localhostおよびLAN内にはPingできません\n||多分...||", color=0x00ff00))
            return
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


class ping(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        datas = json.load(open(f'{dir}/setting.json', 'r'))["database_data"]
        self.client = HTTP_db.Client(
            url=datas["address"], port=datas["port"], intkey=True)

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
    bot.add_cog(ping(bot))
