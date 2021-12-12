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

global task


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
            await mes.edit(content=f"{i}ﾀﾞｯﾀﾖｰ")
            return
        elif ctx.message.content == "n!test 5":
            await ctx.message.channel.send(test_id)
            return



def setup(bot):
    bot.add_cog(test(bot))