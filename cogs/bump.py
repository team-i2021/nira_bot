from discord.ext import commands
import discord
import datetime
import pickle
import re
import random
import asyncio
import time
import math

import sys
from cogs.embed import embed
sys.path.append('../')
from util import admin_check, n_fc, eh
import util.srtr as srtr

#Bump通知

class bump(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.command()
    async def bump(self, ctx: commands.Context):
        if ctx.message.content == "n!bump":
            if ctx.message.guild.id not in n_fc.bump_list:
                await ctx.message.reply(embed=discord.Embed(title="Bump通知", description=f"{ctx.message.guild.name}でBump設定は無効です。", color=0x00ff00))
            else:
                await ctx.message.reply(embed=discord.Embed(title="Bump通知", description=f"{ctx.message.guild.name}でBump設定は有効です。", color=0x00ff00))
            return
        if ctx.message.content == "n!bump on":
            if admin_check.admin_check(ctx.message.guild, ctx.message.author) or ctx.message.author.id in n_fc.py_admin:
                n_fc.bump_list[ctx.message.guild.id] = 1
                await ctx.message.reply(embed=discord.Embed(title="Bump通知", description=f"{ctx.message.guild.name}でBump通知の設定を有効にしました。", color=0x00ff00))
            else:
                await ctx.message.reply(embed=discord.Embed(title="エラー", description=f"管理者権限がありません。", color=0xff0000))
            return
        elif ctx.message.content == "n!bump off":
            if admin_check.admin_check(ctx.message.guild, ctx.message.author) or ctx.message.author.id in n_fc.py_admin:
                del n_fc.bump_list[ctx.message.guild.id]
                await ctx.message.reply(embed=discord.Embed(title="Bump通知", description=f"{ctx.message.guild.name}でBump通知の設定を無効にしました。", color=0x00ff00))
            else:
                await ctx.message.reply(embed=discord.Embed(title="エラー", description=f"管理者権限がありません。", color=0xff0000))
            return
        else:
            await ctx.message.reply(embed=discord.Embed(title="Bump設定", description="`n!bump`:Bump通知の設定の状態表示\n`n!bump on`:サーバーでのBump通知の設定を有効にします。\n`n!bump off`:サーバーでのBump通知の設定を無効にします。", color=0x00ff00))
        return

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild.id not in n_fc.bump_list:
            return
        if message.author.id != 302050872383242240:
            return
        if message.embeds == []:
            return
        if message.embeds[0].title != "DISBOARD: The Public Server List":
            return
        if re.search("Bump done!", message.embeds[0].description):
            print("bump set.")
            await message.channel.send(embed=discord.Embed(title="Bump通知設定", description=f"<t:{math.floor(time.time())+7200}:f>、<t:{math.floor(time.time())+7200}:R>に通知します。", color=0x00ff00))
            await asyncio.sleep(7200)
            bump_rnd = random.randint(1,3)
            if bump_rnd == 1:
                await message.channel.send(embed=discord.Embed(title="Bumpの時間よ！", description=f"Bumpしたければすればいいんじゃないの...？(ツンデレ)\n```!d bump```", color=0x00ff00))
            elif bump_rnd == 2:
                await message.channel.send(embed=discord.Embed(title="Bumpしやがれください！", description=f"お前がBumpするんだよ、あくしろよ！\n```!d bump```", color=0x00ff00))
            elif bump_rnd == 3:
                await message.channel.send(embed=discord.Embed(title="Bumpしましょう！", description=f"Bumpの時間ですよ！\n```!d bump```", color=0x00ff00))
            return

def setup(bot):
    bot.add_cog(bump(bot))