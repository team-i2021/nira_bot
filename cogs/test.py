from contextlib import redirect_stdout
import discord
from discord import message
from discord.ext import commands
from discord.ext.commands.bot import Bot
from discord.utils import get
from os import getenv
import sys
import os
import re
import random
import a2s
import asyncio
import datetime
import math

global task


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


#残骸だよ

def server_check(embed, type, g_id, n):
    sv_ad = ("0.0.0.0", 0)
    sv_nm = "ServerName(Virtual)"
    sv_dt = "None"
    try:
        sv_dt = a2s.SourceInfo(protocol=17, server_name='VirtualNetwork', map_name='VirtualMap', folder='virtual_games', game='VirtualGame', app_id=0, player_count=2, max_players=20, bot_count=0, server_type='d', platform='w', password_protected=True, vac_enabled=True, version='1.0.0.0', edf=177, port=80, steam_id=1, stv_port=None, stv_name=None, keywords=',OWNINGID:90154007008706560,OWNINGNAME:90154007008706560,NUMOPENPUBCONN:20,P2PADDR:1,P2PPORT:80,LEGACY_i:0', game_id=1, ping=0.001)
        if type == 0:
            embed.add_field(name=f"> {sv_dt.server_name} - {sv_dt.map_name}", value="OK", inline=False)
        elif type == 1:
            embed.add_field(name=f"> {sv_nm}", value=f"```{sv_dt}```", inline=False)
        user = ""
        sv_us = [a2s.Player(index=0, name='NattyanTV - Virtual1', score=0, duration=210.8592071533203), a2s.Player(index=0, name='NattyanTV - Virtual2', score=0, duration=2100.8592071533203)]
        if type == 0:
            if sv_us != []:
                logging.info(f"{sv_us[0].name}")
                for i in range(len(sv_us)):
                    user_add = str(sv_us[i].name)
                    user_time = int(sv_us[i].duration)
                    if user_time >= 60:
                        user_time = f"{user_time // 60}時間{user_time % 60}"
                    if user_add != "":
                        user = user + "\n" + f"```{user_add} | {user_time}分```"
                if user == "":
                    user = "（ユーザーデータが取得出来ませんでした。）"
                embed.add_field(name="> Online User", value=f"content数:{len(sv_us)}人{user}\n==========", inline=False)
            else:
                embed.add_field(name="> Online User", value=":information_source:オンラインユーザーはいません。\n==========", inline=False)
        elif type == 1:
            embed.add_field(name="> Online User", value=f"```{sv_us}```", inline=False)
    except BaseException as err:
        if str(err) == "timed out":
            if type == 0:
                embed.add_field(name=f"> {sv_nm}", value=":ng:サーバーに接続できませんでした。(タイムアウト)\n==========", inline=False)
            if type == 1:
                embed.add_field(name=f"> {sv_nm}", value=f"```{err}```", inline=False)
        else:
            logging.error(f"an error has occured during ServerStatus checking\n{err}")
            if type == 0:
                embed.add_field(name=f"> {sv_nm}", value=":x:不明なエラーが発生しました。\n==========", inline=False)
            if type == 1:
                embed.add_field(name=f"> {sv_nm}", value=f"```{sys.exc_info()}```", inline=False)
    return True

def ss_pin_embed(embed):
    sv_ad = ("0.0.0.0",0)
    sv_nm = "TEST"
    sv_dt = "None"
    print(f"{sv_ad}/{sv_nm}")
    try:
        sv_dt = a2s.SourceInfo(protocol=17, server_name='VirtualNetwork', map_name='VirtualMap', folder='virtual_games', game='VirtualGame', app_id=0, player_count=2, max_players=20, bot_count=0, server_type='d', platform='w', password_protected=True, vac_enabled=True, version='1.0.0.0', edf=177, port=80, steam_id=1, stv_port=None, stv_name=None, keywords=',OWNINGID:90154007008706560,OWNINGNAME:90154007008706560,NUMOPENPUBCONN:20,P2PADDR:1,P2PPORT:80,LEGACY_i:0', game_id=1, ping=0.001)
        embed.add_field(name=f"> {sv_dt.server_name} - {sv_dt.map_name}", value=":white_check_mark:オンライン", inline=False)
        print(f"Online:{sv_dt}")
        user = ""
        sv_us = [a2s.Player(index=0, name='NattyanTV - Virtual1', score=0, duration=210.8592071533203), a2s.Player(index=0, name='NattyanTV - Virtual2', score=0, duration=2100.8592071533203)]
        print(f"Users:{sv_us}")
        if sv_us != []:
            for i in range(len(sv_us)):
                print("range")
                user_add = str(sv_us[i].name)
                user_time = int(sv_us[i].duration/60)
                if user_time >= 60:
                    user_time = f"{int(user_time // 60)}時間{int(user_time % 60)}"
                if user_add != "":
                    user = user + "\n" + f"```{user_add} | {user_time}分```"
            if user == "":
                user = "（ユーザーデータが取得出来ませんでした。）"
            embed.add_field(name="> Online User", value=f"プレーヤー数:{len(sv_us)}人{user}\n==========", inline=False)
        else:
            embed.add_field(name="> Online User", value=":information_source:オンラインユーザーはいません。\n==========", inline=False)
    except BaseException as err:
        if str(err) == "timed out":
            if type == 0:
                embed.add_field(name=f"> {sv_nm}", value=":ng:サーバーに接続できませんでした。(タイムアウト)\n==========", inline=False)
            if type == 1:
                embed.add_field(name=f"> {sv_nm}", value=f"```{err}```", inline=False)
        else:
            logging.error(f"an error has occured during ServerStatus checking\n{err}")
            if type == 0:
                embed.add_field(name=f"> {sv_nm}", value=":x:不明なエラーが発生しました。\n==========", inline=False)
            if type == 1:
                embed.add_field(name=f"> {sv_nm}", value=f"```{err}```", inline=False)
    print(f"Script end")
    return True

#TEST
test_id = 2

class test(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        
    @commands.command()
    @commands.cooldown(1, 3, type=commands.BucketType.guild)
    async def test(self, ctx: commands.Context):
        if ctx.message.content == "n!test 1":
            await ctx.message.channel.send(0/0)
            return
        elif ctx.message.content == "n!test 2":
            await ctx.message.channel.send("test")
            return
        elif ctx.message.content == "n!test 3":
            await ctx.message.channel.send("ﾅｲﾖｰ")
            return
        elif ctx.message.content == "n!test 4":
            mes = await ctx.message.channel.send("ｹｲｿｸｽﾙﾖｰ")
            for i in range(18):
                pass
            await mes.edit(content=f"{i}ﾀﾞｯﾀﾖｰ\n{range(18)}")
            return
        elif ctx.message.content == "n!test 5":
            await ctx.message.channel.send(test_id)
            return
        elif ctx.message.content == "n!test 6":
            embed = discord.Embed(title="VirtualMode", description=f"{ctx.message.author.mention}\n:globe_with_meridians:ss_test\n==========", color=0x00ff00)
            server_check(embed, 0, ctx.message.guild.id, 1)
            await ctx.reply("TEST Num6(ss)", embed=embed)
            return
        elif ctx.message.content == "n!test 7":
            cont = await ctx.reply("nastu")
            await asyncio.sleep(3)
            embed = discord.Embed(title="natsu", description="natsu", color=0x004400)
            await cont.edit(embed=embed)
            return
        elif ctx.message.content == "n!test 8":
            embed=discord.Embed(title="title",description="description",color=0xffffff)
            ss_pin_embed(embed)
            await ctx.reply(embed=embed)



def setup(bot):
    bot.add_cog(test(bot))