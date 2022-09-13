import listre
import logging
import random
import re
import sys


import nextcord
from nextcord import Interaction, SlashOption
from nextcord.ext import commands

from util.n_fc import GUILD_IDS
from util.nira import NIRA


GODS = [
    "ブラフマー",
    "ヴィシュヌ",
    "シヴァ",
    "ガネーシャ",
    "ハヌマーン",
    "クリシュナ",
    "サラスヴァティー",
    "ラクシュミー",
    "パールヴァティー",
    "ドゥルガー",
    "スカンダ",
    "カーリー",
    "ラーマ"
]

class Gacha(commands.Cog):
    def __init__(self, bot: NIRA, **kwargs):
        self.bot = bot

    @nextcord.slash_command(name="gacha", description="The command of amuse", guild_ids=GUILD_IDS)
    async def gacha(self, interaction: Interaction):
        pass

    @gacha.subcommand(name="india", description="古代インドピックアップ確定ガチャ")
    async def normal(
            self,
            interaction: Interaction,
            count: int = SlashOption(
                name="回数",
                description="ガチャの回数",
                required=True,
                choices={"1連分": 1, "10連分": 10}
            )
        ):
        text = ""
        for i in range(count):
            item = GODS[random.randint(1, len(GODS)) - 1]
            rare = random.randint(1, 10000) / 100
            if rare <= 20:
                rare_text = 1
            elif rare <= 50:
                rare_text = 2
            elif rare <= 90:
                rare_text = 3
            elif rare <= 97.5:
                rare_text = 4
            elif rare <= 100:
                rare_text = 5
            else:
                rare_text = 1
            text += f"{'★' * rare_text} - {item}\n"
        embed = nextcord.Embed(title=f"古代インドピックアップ確定ガチャ {count}連分", description=text, color=0x333333)
        await interaction.send(embed=embed)


def setup(bot, **kwargs):
    bot.add_cog(Gacha(bot, **kwargs))
