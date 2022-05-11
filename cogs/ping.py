import asyncio
from nextcord.ext import commands
import nextcord
import subprocess
import traceback
from subprocess import PIPE
import os
import sys
from nextcord import Interaction, SlashOption, ChannelType

sys.path.append('../')
from util import admin_check, n_fc, eh
#pingを送信するだけ



#loggingの設定
import logging
dir = sys.path[0]
class NoTokenLogFilter(logging.Filter):
    def filter(self, record):
        message = record.getMessage()
        return 'token' not in message

logger = logging.getLogger(__name__)
logger.addFilter(NoTokenLogFilter())
formatter = '%(asctime)s$%(filename)s$%(lineno)d$%(funcName)s$%(levelname)s:%(message)s'
logging.basicConfig(format=formatter, filename=f'{dir}/nira.log', level=logging.INFO)

async def ping_there(ctx, adr, type):
    if type == 1:
        async with ctx.channel.typing():
            res = subprocess.run(f"ping {adr} -c 4 -W 3", stdout=PIPE, stderr=PIPE, shell=True, text=True)
            if res.returncode == 0:
                await ctx.reply(f"`{adr}`に接続できました。\n```{res.stdout}```")
            else:
                await ctx.reply(f"`{adr}`に接続できませんでした。")
            return
    elif type == 0:
        res = subprocess.run(f"ping {adr} -c 4 -W 3", stdout=PIPE, stderr=PIPE, shell=True, text=True)
        if res.returncode == 0:
            await ctx.followup.send(f"`{adr}`に接続できました。\n```{res.stdout}```")
        else:
            await ctx.followup.send(f"`{adr}`に接続できませんでした。")

#ctx.message == None:こまんど
async def base_ping(bot, ctx: commands.Context, adr):
    if type(ctx) == Interaction and adr == None:
        logger.info(f"DiscordサーバーとのPing値：{round(bot.latency * 1000)}ms")
        await ctx.followup.send(embed=nextcord.Embed(title="Ping", description=f"現在のPing値は`{round(bot.latency * 1000)}`msです。", color=0x00ff00))
        return
    elif type(ctx) == Interaction == None and adr != None:
        if adr[8:] == "192.168." or adr == "127.0.0.1" or adr == "localhost" or adr == "0.0.0.0" or adr == "127.0.1" or adr == "127.1" or adr == "2130706433" or adr == "0x7F000001" or adr == "017700000001":
            if ctx.author.id not in n_fc.py_admin:
                await ctx.followup.send(embed=nextcord.Embed(title="Ping", description=f"localhostおよびLAN内にはPingできません\n||多分...||",color=0xff0000),ephemeral=True)
                return
        try:
            await asyncio.wait_for(ping_there(ctx, adr, 0), timeout=8)
            return
        except BaseException as err:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            logging.error(f"大変申し訳ございません。エラーが発生しました。\n```{err}```\n```sh\n{sys.exc_info()}```\nfile:`{fname}`\nline:{exc_tb.tb_lineno}")
            await ctx.followup.send(embed=nextcord.Embed(title="Ping", description=f"エラーが発生しました。\n```sh\n{traceback.format_exc()}```",color=0xff0000),ephemeral=True)
            # await ctx.respond(f"{adr}に時間内に接続できませんでした。")
        return
    if ctx.message != None:
        if adr == None:
            embed = nextcord.Embed(title="Ping", description=f"現在のPing値は`{round(bot.latency * 1000)}`msです。", color=0x00ff00)
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

    @nextcord.slash_command(name="ping", description="Discordサーバー又は、指定サーバーとのレイテンシを計測します。")
    async def ping_slash(
        self,
        interaction = Interaction,
        address: str = SlashOption(
            name="address",
            description="アドレス。指定しないとDiscordサーバーとのRTTを表示します。",
            required=False,
        )
        ):
        await interaction.response.defer()
        await base_ping(self.bot, interaction, address)

    @commands.command(name="ping", help="""\
レイテンシを表示します。
`n!ping`で、DiscordサーバーとBOTサーバーとのレイテンシを表示します。
`n!ping [address]`という風に、アドレスを指定すると、そのアドレスとのpingを測定します。
ローカルIP及びlocalhostにはping出来ません。多分....。
また、pingは実測値ですが、当然参考値にしてください。

引数1:address(str)
IPアドレスまたはドメインの形で指定してください。""")
    async def ping(self, ctx: commands.Context):
        texts = ctx.message.content.split(" ",1)
        if len(texts) == 1:
            await base_ping(self.bot, ctx, None)
        else:
            await base_ping(self.bot, ctx, texts[1])

def setup(bot):
    bot.add_cog(ping(bot))
