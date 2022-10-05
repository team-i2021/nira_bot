import asyncio
import importlib
import os
import sys

import HTTP_db
import nextcord
from nextcord.ext import commands

from util import eh, srtr, database
from util.n_fc import GUILD_IDS
from util.nira import NIRA

SYSDIR = sys.path[0]
START = ["start", "on", "play", "スタート", "はじめ"]
STOP = ["stop", "off", "end", "exit", "ストップ", "おわり"]

# しりとり管理系

class srtr_data:
    name = "srtr_data"
    value = {}
    default = {}
    value_type = database.CHANNEL_VALUE

class Siritori(commands.Cog):
    def __init__(self, bot: NIRA, **kwargs):
        self.bot = bot

    @nextcord.slash_command(name="srtr", description="Siritori", guild_ids=GUILD_IDS)
    async def srtr(self):
        pass

    async def srtr_control(self, start: bool, guild, channel) -> nextcord.Embed:
        await database.default_pull(self.bot.client, srtr_data)

        if start:
            if guild.id not in srtr_data.value:
                srtr_data.value[guild.id] = {}

            if channel.id in srtr_data.value[guild.id]:
                return nextcord.Embed(title="しりとり", description=f"{channel.name}でしりとりは既に実行されています。", color=0x00ff00)

            try:
                srtr_data.value[guild.id][channel.id] = 1
                await database.default_push(self.bot.client, srtr_data)

            except Exception as err:
                return eh(self.bot.client, err)

            return nextcord.Embed(title="しりとり", description=f"{channel.name}でしりとりを始めます。", color=0x00ff00)

        else:
            if guild.id not in srtr_data.value or channel.id not in srtr_data.value[guild.id]:
                return nextcord.Embed(title="しりとり", description=f"{channel.name}でしりとりは実行されていません。", color=0x00ff00)

            try:
                del srtr_data.value[guild.id][channel.id]
                await database.default_push(self.bot.client, srtr_data)

            except Exception as err:
                return eh(self.bot.client, err)

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
            embed = await self.srtr_control(
                True, ctx.guild, ctx.channel)

        elif control_arg in STOP:
            embed = await self.srtr_control(
                False, ctx.guild, ctx.channel)

        else:
            embed = nextcord.Embed(
                title="しりとり",
                description=f"`{self.bot.command_prefix}srtr start`でそのチャンネルでしりとり（風対話）を実行し、`{self.bot.command_prefix}srtr stop`でしりとりを停止します。",
                color=0x00ff00
            )

        await ctx.reply(embed=embed)


    @srtr.subcommand(name="start", description="Start Siritori game", description_localizations={nextcord.Locale.ja: "しりとり風のゲームで遊びます"})
    async def srtr_start(self, interaction: nextcord.Interaction):
        await interaction.response.defer()
        await interaction.send(embed=(await self.srtr_control(True, interaction.guild, interaction.channel)))


    @srtr.subcommand(name="stop", description="Stop Siritori game", description_localizations={nextcord.Locale.ja: "しりとり風のゲームを終了します"})
    async def srtr_stop(self, interaction: nextcord.Interaction):
        await interaction.response.defer()
        await interaction.send(embed=(await self.srtr_control(False, interaction.guild, interaction.channel)))


    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message):
        if not isinstance(message.channel, nextcord.DMChannel):
            await database.default_pull(self.bot.client, srtr_data)
            if message.guild.id in srtr_data.value:
                if message.channel.id in srtr_data.value[message.guild.id]:
                    await srtr.on_srtr(message, self.bot.client)



def setup(bot, **kwargs):
    importlib.reload(srtr)
    bot.add_cog(Siritori(bot, **kwargs))
