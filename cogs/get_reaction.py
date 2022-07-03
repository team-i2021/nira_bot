import logging
import os
import pickle
import requests
import sys

import nextcord
from nextcord.ext import commands

from cogs import server_status
from util import admin_check, n_fc, eh

SYSDIR = sys.path[0]

class GetReaction(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: nextcord.Reaction, member: nextcord.Member):
        if member.id != self.bot.user.id and reaction.message.author.id == self.bot.user.id and str(reaction.emoji) == '<:trash:908565976407236608>':
            await reaction.message.delete()
            return


def setup(bot):
    bot.add_cog(GetReaction(bot))
