from discord.ext import commands
import discord

import sys
sys.path.append('../')
from util import admin_check, n_fc, eh

#管理者かどうかをチェックする

class check(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def admin(self, ctx: commands.Context):
        if admin_check.admin_check(ctx.message.guild, ctx.message.author):
            await ctx.message.reply(embed=discord.Embed(title="ADMIN", description=f"権限があるようです。", color=0x00ff00))
        elif ctx.message.author.id in n_fc.py_admin:
            await ctx.message.reply(embed=discord.Embed(title="ADMIN", description=f"サーバー権限はありませんが、コマンドは実行できます。(開発者)\n**開発者として不用意な行動は慎んでください。**", color=0xffff00))
        else:
            await ctx.message.reply(embed=discord.Embed(title="ADMIN", description=f"権限がないようです。\n**（管理者権限を付与したロールがありませんでした。）**\n自分が管理者の場合は、自分に管理者権限を付与したロールを付けてください。", color=0xff0000))
        return

def setup(bot):
    bot.add_cog(check(bot))