from nextcord.ext import commands
import nextcord
import pickle
import importlib

import sys
sys.path.append('../')
from util import admin_check, n_fc, eh, srtr, word_data

from nira import home_dir

#しりとり管理系

class siritori(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def srtr(self, ctx: commands.Context):
        if ctx.message.content == "n!srtr start":
            try:
                if ctx.message.guild.id in n_fc.srtr_bool_list:
                    if ctx.message.channel.id in n_fc.srtr_bool_list:
                        embed = nextcord.Embed(title="しりとり", description=f"{ctx.message.channel.name}でしりとりは既にに実行されています。", color=0x00ff00)
                        await ctx.message.reply(embed=embed)
                        return
                    else:
                        n_fc.srtr_bool_list[ctx.message.guild.id] = {ctx.message.channel.id:1}
                if ctx.message.guild.id not in n_fc.srtr_bool_list:
                    n_fc.srtr_bool_list[ctx.message.guild.id] = {ctx.message.channel.id:1}
                    with open(f'{home_dir}/srtr_bool_list.nira', 'wb') as f:
                        pickle.dump(n_fc.srtr_bool_list, f)
            except BaseException as err:
                    await ctx.message.reply(embed=eh(err))
                    return
            embed = nextcord.Embed(title="しりとり", description=f"{ctx.message.channel.name}でしりとりを始めます。", color=0x00ff00)
            await ctx.message.reply(embed=embed)
            return
        elif ctx.message.content == "n!srtr stop":
            try:
                if ctx.message.guild.id not in n_fc.srtr_bool_list:
                    embed = nextcord.Embed(title="しりとり", description=f"{ctx.message.guild.name}でしりとりは実行されていません。", color=0x00ff00)
                    await ctx.message.reply(embed=embed)
                    return
                if ctx.message.channel.id not in n_fc.srtr_bool_list[ctx.message.guild.id]:
                    embed = nextcord.Embed(title="しりとり", description=f"{ctx.message.channel.name}でしりとりは実行されていません。", color=0x00ff00)
                    await ctx.message.reply(embed=embed)
                    return
                del n_fc.srtr_bool_list[ctx.message.guild.id][ctx.message.channel.id]
                with open(f'{home_dir}/srtr_bool_list.nira', 'wb') as f:
                        pickle.dump(n_fc.srtr_bool_list, f)
            except BaseException as err:
                await ctx.message.reply(embed=eh(err))
            embed = nextcord.Embed(title="しりとり", description=f"{ctx.message.channel.name}でのしりとりを終了します。", color=0x00ff00)
            await ctx.message.reply(embed=embed)
            return
        elif ctx.message.content == "n!srtr reload" and ctx.message.author.id in n_fc.py_admin:
            try:
                importlib.reload(srtr)
                await ctx.reply("Reloaded.")
            except BaseException as err:
                await ctx.reply(f"err:`{str(err)}`")
        else:
            embed = nextcord.Embed(title="しりとり", description=f"`n!srtr start`でそのチャンネルでしりとり（風対話）を実行し、`n!srtr stop`でしりとりを停止します。", color=0x00ff00)
            await ctx.message.reply(embed=embed)
            return

def setup(bot):
    bot.add_cog(siritori(bot))
    