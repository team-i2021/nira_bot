import asyncio
from discord.ext import commands
import discord
import subprocess
from subprocess import PIPE
import sys

from discord.ext.commands.errors import CommandNotFound
sys.path.append('../')
from util import admin_check, n_fc, eh
#pingを送信するだけ
from nira import bot as tod

#loggingの設定
import logging
class NoTokenLogFilter(logging.Filter):
    def filter(self, record):
        message = record.getMessage()
        return 'token' not in message

logger = logging.getLogger(__name__)
logger.addFilter(NoTokenLogFilter())
formatter = '%(asctime)s$%(filename)s$%(lineno)d$%(funcName)s$%(levelname)s:%(message)s'
logging.basicConfig(format=formatter, filename='/home/nattyantv/nira.log', level=logging.INFO)

async def ping_there(ctx, adr):
    async with ctx.message.channel.typing():
        res = subprocess.run(f"ping {adr} -c 3 -W 3", stdout=PIPE, stderr=PIPE, shell=True, text=True)
        if res.returncode == 0:
            await ctx.reply(f"`{adr}`に接続できました。\n```{res.stdout}```")
        else:
            await ctx.reply(f"`{adr}`に接続できませんでした。")



async def base_ping(self, ctx: commands.Context, address):
    if address == int:
        adr = ctx.message.content[7:]
    else:
        adr = address
    if ctx.message.content == "n!ping" or adr == None:
        embed = discord.Embed(title="Ping", description=f"現在のPing値は`{round(self.bot.latency * 1000)}`msです。", color=0x00ff00)
        logger.info(f"DiscordサーバーとのPing値：{round(self.bot.latency * 1000)}ms")
        await ctx.reply(embed=embed)
        return
    if adr[8:] == "192.168." or adr == "127.0.0.1" or adr == "localhost" or adr == "0.0.0.0" or adr == "127.0.1" or adr == "127.1" or adr == "2130706433" or adr == "0x7F000001" or adr == "017700000001":
        if ctx.message.author.id not in n_fc.py_admin:
            await ctx.reply("localhost及びローカルIPにはping出来ません。")
            return
    try:
        await asyncio.wait_for(ping_there(ctx, adr), timeout=8)
    except asyncio.TimeoutError:
        await ctx.reply(f"{adr}に時間内に接続できませんでした。")
    return

# add == None: スラッシュコマンドで、何も入れなかった場合
# add == str: スラッシュコマンドで、addressを入れた場合
# add == int: 「n!ping」を使った場合

class ping(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @tod.slash_command()
    async def ping(self, ctx: commands.Context, address:str = None):
        await base_ping(self, ctx, address)
    
    @commands.command()
    async def ping(self, ctx: commands.Context):
        address = int
        await base_ping(self, ctx, address)

def setup(bot):
    bot.add_cog(ping(bot))
    tod.add_application_command(ping)