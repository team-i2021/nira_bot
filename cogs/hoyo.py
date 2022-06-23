import logging
from util import admin_check, n_fc, eh
import asyncio
from nextcord.ext import commands
import nextcord
import subprocess
import traceback
from subprocess import PIPE
import os
import sys
from nextcord import Interaction, SlashOption, ChannelType
#import genshin
#from pyngrok import ngrok

sys.path.append('../')

# Genshin...


class Genshin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

#    @nextcord.slash_command(name="genshin", description="Show genshin info", guild_ids=n_fc.GUILD_IDS)
#    async def slash_genshin(self, interaction: Interaction):
#        pass
#
#    @slash_genshin.subcommand(name="stats", description="原神のユーザーの戦績を表示します")
#    async def slash_genshin_stats(self, interaction: Interaction, authkey: str = SlashOption(required=True, description="原神のAuthKey")):
#        await interaction.response.defer()
#        client = genshin.Client(
#            lang="ja-jp", game=genshin.Game.GENSHIN, authkey=authkey)
#        user = await client.get_full_genshin_user(client.uid)
#        # user.stats.
#        embed = nextcord.Embed(
#            title=f"{client.get_banner_names}の戦績", description=f"UID:`{client.uid}`", color=0x00ff00)
#        embed.add_field(name="活動日数", value=f"`{user.stats.days_active}`日")
#        embed.add_field(name="アチーブメント", value=f"`{user.stats.achievements}`個")
#        embed.add_field(name="キャラクター数", value=f"`{user.stats.characters}`人")
#        embed.add_field(name="解放済みワープポイント",
#                        value=f"`{user.stats.unlocked_waypoints}`")
#        embed.add_field(name="宝箱(普通,精巧,貴重,豪華,珍奇)",
#                        value=f"`{[user.stats.common_chests, user.stats.exquisite_chests, user.stats.precious_chests, user.stats.luxurious_chests, user.stats.remarkable_chests]}`")
#        await interaction.followup.send(embed=embed)

    @commands.command(name="genshin", help="""\
原神の情報表示
`n!genshin ...` : 原神の戦績を表示します""")
    async def command_genshin(self, ctx: commands.Context):
        return


def setup(bot):
    bot.add_cog(Genshin(bot))
