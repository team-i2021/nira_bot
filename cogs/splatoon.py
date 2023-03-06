import asyncio
import aiohttp
import ipaddress
import json
import logging
import os
import platform
import subprocess
import sys
import enum
import traceback

import nextcord
from nextcord import Interaction, SlashOption, ChannelType
from nextcord.ext import commands

from util import admin_check, n_fc, eh, database
from util.nira import NIRA

# pingを送信するだけ

class MatchType(enum.Enum):
    RegularMatch = 0
    BankaraMatch = 1
    xMatch = 2


class Splatoon(commands.Cog):
    def __init__(self, bot: NIRA, **kwargs):
        self.bot = bot
        self.urls = {
            "schedule": "https://splatoon3.ink/data/schedules.json",
            "locale_ja-JP": "https://splatoon3.ink/data/locale/ja-JP.json"
        }
        self.locale = {}
        asyncio.ensure_future(self.refresh_locale())

    async def refresh_locale(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(self.urls["locale_ja-JP"]) as resp:
                self.locale = await resp.json()

    async def getSchedule(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(self.urls["schedule"]) as resp:
                return await resp.json()

    async def scheduleEmbed(self, matchtype: MatchType, schedule): 
        if matchtype == MatchType.RegularMatch:
            schedule["data"]["regularSchedules"]["nodes"][0]["regularMatchSetting"]["vsStages"][0]["image"]["url"]

            Stages = {
                "current": schedule["data"]["regularSchedules"]["nodes"][0]["regularMatchSetting"]["vsStages"],
                "next": schedule["data"]["regularSchedules"]["nodes"][1]["regularMatchSetting"]["vsStages"]
            }

            embed = nextcord.Embed(
                title="Regular Match - Current Stage",
                description=f"・{self.locale['stages'][Stages['current'][0]['id']]['name']}\n・{self.locale['stages'][Stages['current'][1]['id']]['name']}",
                color=0x00ff00
            )

            embed.add_field(
                name="Next Stage is...",
                value=f"・{self.locale['stages'][Stages['next'][0]['id']]['name']}\n・{self.locale['stages'][Stages['next'][1]['id']]['name']}",
                inline=False
            )

            embed.set_author(name="Splatoon3", icon_url="https://splatoon3.ink/assets/little-buddy.445c3c88.png")

        else:
            embed = nextcord.Embed(title="Not supported match type.", description="Not support or currently not supported.", color=0xff0000)

        return embed


    @nextcord.slash_command(name="splatoon", description="Splatoon command", guild_ids=n_fc.GUILD_IDS)
    async def splatoon_slash(
            self,
            interaction: Interaction
        ):
        pass

    @splatoon_slash.subcommand(name="stage", description="Stage")
    async def stage_splatoon_slash(
            self,
            interaction: Interaction,
            matchtype: int = SlashOption(
                name="matchtype",
                description="Type of match",
                required=True,
                choices={"レギュラーマッチ": 0, "バンカラマッチ": 1, "Xマッチ": 2},
            ),
        ):
        await interaction.response.defer(ephemeral=True)
        await interaction.send(embed=(await self.scheduleEmbed(MatchType(matchtype), (await self.getSchedule()))))


def setup(bot, **kwargs):
    bot.add_cog(Splatoon(bot, **kwargs))
