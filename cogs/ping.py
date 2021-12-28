import asyncio
from discord.ext import commands
import discord
import subprocess
from subprocess import PIPE
import os
import sys

from discord.ext.commands.errors import CommandNotFound
sys.path.append('../')
from util import admin_check, n_fc, eh
#pingを送信するだけ



#loggingの設定
import logging

class NoTokenLogFilter(logging.Filter):
    def filter(self, record):
        message = record.getMessage()
        return 'token' not in message

logger = logging.getLogger(__name__)
logger.addFilter(NoTokenLogFilter())
formatter = '%(asctime)s$%(filename)s$%(lineno)d$%(funcName)s$%(levelname)s:%(message)s'
logging.basicConfig(format=formatter, filename=f'/home/nattyantv/nira_bot_rewrite/nira.log', level=logging.INFO)

async def ping_there(ctx, adr, type):
    if type == 1:
        async with ctx.channel.typing():
            res = subprocess.run(f"ping {adr} -c 3 -W 3", stdout=PIPE, stderr=PIPE, shell=True, text=True)
            if res.returncode == 0:
                await ctx.reply(f"`{adr}`に接続できました。\n```{res.stdout}```")
            else:
                await ctx.reply(f"`{adr}`に接続できませんでした。")
    elif type == 0:
        res = subprocess.run(f"ping {adr} -c 3 -W 3", stdout=PIPE, stderr=PIPE, shell=True, text=True)
        if res.returncode == 0:
            await ctx.respond(f"`{adr}`に接続できました。\n```{res.stdout}```")
        else:
            await ctx.respond(f"`{adr}`に接続できませんでした。")

#ctx.message == None:こまんど
async def base_ping(bot, ctx: commands.Context, adr):
    if ctx.message == None and adr == None:
        embed = discord.Embed(title="Ping", description=f"現在のPing値は`{round(bot.latency * 1000)}`msです。", color=0x00ff00)
        logger.info(f"DiscordサーバーとのPing値：{round(bot.latency * 1000)}ms")
        await ctx.respond(embed=embed)
        return
    elif ctx.message == None and adr != None:
        if adr[8:] == "192.168." or adr == "127.0.0.1" or adr == "localhost" or adr == "0.0.0.0" or adr == "127.0.1" or adr == "127.1" or adr == "2130706433" or adr == "0x7F000001" or adr == "017700000001":
            if ctx.author.id not in n_fc.py_admin:
                await ctx.respond("localhost及びローカルIPにはping出来ません。")
                return
        try:
            await asyncio.wait_for(ping_there(ctx, adr, 0), timeout=8)
            return
        except BaseException as err:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            logging.error(f"大変申し訳ございません。エラーが発生しました。\n```{err}```\n```sh\n{sys.exc_info()}```\nfile:`{fname}`\nline:{exc_tb.tb_lineno}")
            # await ctx.respond(f"{adr}に時間内に接続できませんでした。")
        return
    if ctx.message != None:
        if ctx.message.content == "n!ping":
            embed = discord.Embed(title="Ping", description=f"現在のPing値は`{round(bot.latency * 1000)}`msです。", color=0x00ff00)
            logger.info(f"DiscordサーバーとのPing値：{round(bot.latency * 1000)}ms")
            await ctx.reply(embed=embed)
            return
        elif ctx.message.content != "n!ping":
            if adr[8:] == "192.168." or adr == "127.0.0.1" or adr == "localhost" or adr == "0.0.0.0" or adr == "127.0.1" or adr == "127.1" or adr == "2130706433" or adr == "0x7F000001" or adr == "017700000001":
                if ctx.message.author.id not in n_fc.py_admin:
                    await ctx.reply("localhost及びローカルIPにはping出来ません。")
                    return
            try:
                await asyncio.wait_for(ping_there(ctx, adr, 1), timeout=8)
                return
            except asyncio.TimeoutError:
                await ctx.reply(f"{adr}に時間内に接続できませんでした。")
            return
        return
    return


class ping(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.command()
    async def ping(self, ctx: commands.Context):
        address = ctx.message.content[7:]
        await base_ping(self.bot, ctx, address)

def setup(bot):
    bot.add_cog(ping(bot))
    