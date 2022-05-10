import importlib
import os
import pickle

import nextcord
from nextcord.ext import commands

from util import eh, srtr
from util.n_fc import GUILD_IDS, srtr_bool_list

home_dir = os.path.dirname(__file__)[:-4]
# しりとり管理系


class siritori(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @nextcord.slash_command(name="srtr", description="しりとり", guild_ids=GUILD_IDS)
    async def srtr(self):
        pass

    def srtr_control(self, start: bool, guild, channel) -> nextcord.Embed:
        if start:
            if guild.id not in srtr_bool_list:
                srtr_bool_list[guild.id] = {}

            if channel.id in srtr_bool_list[guild.id]:
                return nextcord.Embed(title="しりとり", description=f"{channel.name}でしりとりは既に実行されています。", color=0x00ff00)

            try:
                srtr_bool_list[guild.id][channel.id] = 1
                with open(f"{home_dir}/srtr_bool_list.nira", "wb") as f:
                    pickle.dump(srtr_bool_list, f)
            except BaseException as err:
                return eh(err)

            return nextcord.Embed(title="しりとり", description=f"{channel.name}でしりとりを始めます。", color=0x00ff00)

        else:
            if guild.id not in srtr_bool_list or channel.id not in srtr_bool_list[guild.id]:
                return nextcord.Embed(title="しりとり", description=f"{channel.name}でしりとりは実行されていません。", color=0x00ff00)

            try:
                del srtr_bool_list[guild.id][channel.id]
                with open(f"{home_dir}/srtr_bool_list.nira", "wb") as f:
                    pickle.dump(srtr_bool_list, f)
            except BaseException as err:
                return eh(err)

            return nextcord.Embed(title="しりとり", description=f"{channel.name}でのしりとりを終了します。", color=0x00ff00)

    @commands.command(name="srtr", help="""\
    しりとり風のゲームで遊ぶことが出来ます。
    漢字には弱いです。

    ・使い方
    `n!srtr start`: そのチャンネルでしりとりゲームを始めます
    `n!srtr stop`: チャンネルのしりとりゲームを終了します


    """)
    async def srtr_ctx(self, ctx: commands.Context):
        if ctx.message.content == "n!srtr start":
            embed = self.srtr_control(True, ctx.message.guild, ctx.message.channel)

        elif ctx.message.content == "n!srtr stop":
            embed = self.srtr_control(False, ctx.message.guild, ctx.message.channel)

        else:
            embed = nextcord.Embed(
                title="しりとり",
                description="`n!srtr start`でそのチャンネルでしりとり（風対話）を実行し、`n!srtr stop`でしりとりを停止します。",
                color=0x00ff00
            )

        await ctx.message.reply(embed=embed)
        return

    @srtr.subcommand(name="start", description="しりとり風のゲームで遊びます")
    async def srtr_start(self, interaction: nextcord.Interaction):
        await interaction.response.send_message(embed=self.srtr_control(True, interaction.guild, interaction.channel))
        return

    @srtr.subcommand(name="stop", description="チャンネルのしりとりゲームを終了します")
    async def srtr_stop(self, interaction: nextcord.Interaction):
        await interaction.response.send_message(embed=self.srtr_control(False, interaction.guild, interaction.channel))
        return


def setup(bot):
    importlib.reload(srtr)
    bot.add_cog(siritori(bot))
