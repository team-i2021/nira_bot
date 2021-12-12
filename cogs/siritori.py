from discord.ext import commands
import discord
import pickle

import sys
sys.path.append('../')
from util import admin_check, n_fc, eh

#しりとり管理系

class siritori(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def srtr(self, ctx: commands.Context):
        if ctx.message.content == "n!srtr":
            embed = discord.Embed(title="しりとり", description=f"`n!srtr start`でそのチャンネルでしりとり（風対話）を実行し、`n!srtr stop`でしりとりを停止します。", color=0x00ff00)
            await ctx.message.reply(embed=embed)
            return
        if ctx.message.content == "n!srtr start":
            try:
                if ctx.message.guild.id in n_fc.srtr_bool_list:
                    if ctx.message.channel.id in n_fc.srtr_bool_list:
                        embed = discord.Embed(title="しりとり", description=f"{ctx.message.channel.name}でしりとりは既にに実行されています。", color=0x00ff00)
                        await ctx.message.reply(embed=embed)
                        return
                    else:
                        n_fc.srtr_bool_list[ctx.message.guild.id] = {ctx.message.channel.id:1}
                if ctx.message.guild.id not in n_fc.srtr_bool_list:
                    n_fc.srtr_bool_list[ctx.message.guild.id] = {ctx.message.channel.id:1}
                    with open('/home/nattyantv/nira_bot_rewrite/srtr_bool_list.nira', 'wb') as f:
                        pickle.dump(n_fc.srtr_bool_list, f)
            except BaseException as err:
                    await ctx.message.reply(embed=eh(err))
                    return
            embed = discord.Embed(title="しりとり", description=f"{ctx.message.channel.name}でしりとりを始めます。", color=0x00ff00)
            await ctx.message.reply(embed=embed)
            return
        if ctx.message.content == "n!srtr stop":
            try:
                if ctx.message.guild.id not in n_fc.srtr_bool_list:
                    embed = discord.Embed(title="しりとり", description=f"{ctx.message.guild.name}でしりとりは実行されていません。", color=0x00ff00)
                    await ctx.message.reply(embed=embed)
                    return
                if ctx.message.channel.id not in n_fc.srtr_bool_list[ctx.message.guild.id]:
                    embed = discord.Embed(title="しりとり", description=f"{ctx.message.channel.name}でしりとりは実行されていません。", color=0x00ff00)
                    await ctx.message.reply(embed=embed)
                    return
                del n_fc.srtr_bool_list[ctx.message.guild.id][ctx.message.channel.id]
                with open('/home/nattyantv/nira_bot_rewrite/srtr_bool_list.nira', 'wb') as f:
                        pickle.dump(n_fc.srtr_bool_list, f)
            except BaseException as err:
                await ctx.message.reply(embed=eh(err))
            embed = discord.Embed(title="しりとり", description=f"{ctx.message.channel.name}でのしりとりを終了します。", color=0x00ff00)
            await ctx.message.reply(embed=embed)
            return

def setup(bot):
    bot.add_cog(siritori(bot))