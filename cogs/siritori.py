import asyncio
import importlib
import os
import sys

import nextcord
from nextcord.ext import commands

from motor import motor_asyncio

from util import eh, srtr, database
from util.n_fc import GUILD_IDS
from util.nira import NIRA

SYSDIR = sys.path[0]
START = ["start", "on", "play", "スタート", "はじめ"]
STOP = ["stop", "off", "end", "exit", "ストップ", "おわり"]

# しりとり管理系


class Siritori(commands.Cog):
    def __init__(self, bot: NIRA, **kwargs):
        self.bot = bot
        self.collection: motor_asyncio.AsyncIOMotorCollection = self.bot.database["siritori_game"]

    @nextcord.slash_command(name="srtr", description="Siritori", guild_ids=GUILD_IDS)
    async def srtr(self, interaction: nextcord.Interaction):
        pass

    async def srtr_control(self, start: bool, guild: nextcord.Guild, channel: nextcord.abc.GuildChannel) -> nextcord.Embed:
        """Control Siritori game"""
        srtr_data = await self.collection.find_one({"guild_id": guild.id})

        if start:
            # Start Siritori game
            if srtr_data is not None:
                if channel.id in srtr_data["channels"]:
                    return nextcord.Embed(title="しりとり", description=f"{channel.name}でしりとりは既に実行されています。", color=0x00ff00)
                else:
                    srtr_data["channels"].append(channel.id)
            else:
                srtr_data = {"guild_id": guild.id, "channels": [channel.id] }

            try:
                await self.collection.update_one({"guild_id": guild.id}, {"$set": srtr_data}, upsert=True)
            except Exception as err:
                return eh(self.bot.client, err)

            return nextcord.Embed(title="しりとり", description=f"{channel.name}でしりとりを始めます。", color=0x00ff00)

        else:
            # Stop Siritori game
            if srtr_data is None or channel.id not in srtr_data["channels"]:
                return nextcord.Embed(title="しりとり", description=f"{channel.name}でしりとりは実行されていません。", color=0x00ff00)

            try:
                srtr_data["channels"].remove(channel.id)
                asyncio.ensure_future(self.collection.update_one({"guild_id": guild.id}, {"$set": srtr_data}, upsert=True))

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
    async def srtr_ctx(self, ctx: commands.Context, control: str | None = None):
        if control in START:
            embed = await self.srtr_control(
                True, ctx.guild, ctx.channel)

        elif control in STOP:
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
            srtr_data = await self.collection.find_one({"guild_id": message.guild.id})
            if srtr_data is not None:
                if message.channel.id in srtr_data[message.guild.id]["value"]:
                    await srtr.on_srtr(message, self.collection)



def setup(bot, **kwargs):
    importlib.reload(srtr)
    bot.add_cog(Siritori(bot, **kwargs))
