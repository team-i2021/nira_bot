import asyncio
from discord.ext import commands
import discord
import subprocess
from subprocess import PIPE
import sys
sys.path.append('../')
from util import admin_check, n_fc, eh
#pingを送信するだけ

async def ping_there(ctx, adr):
    async with ctx.message.channel.typing():
        res = subprocess.run(f"ping {adr} -c 3 -W 3", stdout=PIPE, stderr=PIPE, shell=True, text=True)
        if res.returncode == 0:
            await ctx.reply(f"`{adr}`に接続できました。\n```{res.stdout}```")
        else:
            await ctx.reply(f"`{adr}`に接続できませんでした。")
        

class ping(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx: commands.Context):
        if ctx.message.content == "n!ping":
            embed = discord.Embed(title="Ping", description=f"現在のPing値は`{round(self.bot.latency * 1000)}`msです。", color=0x00ff00)
            await ctx.reply(embed=embed)
            return
        adr = ctx.message.content[7:]
        if adr[8:] == "192.168." or adr == "127.0.0.1" or adr == "localhost" or adr == "0.0.0.0" or adr == "127.0.1" or adr == "127.1" or adr == "2130706433" or adr == "0x7F000001" or adr == "017700000001":
            if ctx.message.author.id not in n_fc.py_admin:
                await ctx.reply("localhost及びローカルIPにはping出来ません。")
                return
        try:
            await asyncio.wait_for(ping_there(ctx, adr), timeout=8)
        except asyncio.TimeoutError:
            await ctx.reply(f"{adr}に時間内に接続できませんでした。")
        return




def setup(bot):
    bot.add_cog(ping(bot))