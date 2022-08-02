import importlib
import os
import pickle
import sys

import nextcord
from nextcord.ext import commands

from util import eh, srtr
from util.n_fc import GUILD_IDS, srtr_bool_list

SYSDIR = sys.path[0]
START = ["start", "on", "play", "スタート", "はじめ"]
STOP = ["stop", "off", "end", "exit", "ストップ", "おわり"]

# しりとり管理系


class Siritori(commands.Cog):
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
                with open(f"{SYSDIR}/srtr_bool_list.nira", "wb") as f:
                    pickle.dump(srtr_bool_list, f)
            except BaseException as err:
                return eh(err)

            return nextcord.Embed(title="しりとり", description=f"{channel.name}でしりとりを始めます。", color=0x00ff00)

        else:
            if guild.id not in srtr_bool_list or channel.id not in srtr_bool_list[guild.id]:
                return nextcord.Embed(title="しりとり", description=f"{channel.name}でしりとりは実行されていません。", color=0x00ff00)

            try:
                del srtr_bool_list[guild.id][channel.id]
                with open(f"{SYSDIR}/srtr_bool_list.nira", "wb") as f:
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


    """, aliases=["しりとり", "siritori"])
    async def srtr_ctx(self, ctx: commands.Context):
        if len(ctx.message.content.split(" ", 1)) == 1:
            embed = nextcord.Embed(
                title="しりとり",
                description=f"`{self.bot.command_prefix}srtr start`でそのチャンネルでしりとり（風対話）を実行し、`{self.bot.command_prefix}srtr stop`でしりとりを停止します。",
                color=0x00ff00
            )
            await ctx.reply(embed=embed)
            return

        control_arg = ctx.message.content.split(" ", 1)[1]

        if control_arg in START:
            embed = self.srtr_control(
                True, ctx.message.guild, ctx.message.channel)

        elif control_arg in STOP:
            embed = self.srtr_control(
                False, ctx.message.guild, ctx.message.channel)

        else:
            embed = nextcord.Embed(
                title="しりとり",
                description=f"`{self.bot.command_prefix}srtr start`でそのチャンネルでしりとり（風対話）を実行し、`{self.bot.command_prefix}srtr stop`でしりとりを停止します。",
                color=0x00ff00
            )

        await ctx.reply(embed=embed)
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
    bot.add_cog(Siritori(bot))
