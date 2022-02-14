from nextcord.ext import commands
import nextcord
import re

import sys
sys.path.append('../')
from util import admin_check, n_fc, eh

#embedを送信する機能

class embed(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.command()
    async def embed(self, ctx: commands.Context):
        if ctx.message.content == "n!embed":
            embed = nextcord.Embed(title="Error", description="構文が間違っています。\n```n!embed [color(000000～ffffff)] [title]\n[description]```", color=0xff0000)
            await ctx.message.reply(embed=embed)
            return
        try:
            mes_ch = ctx.message.content.splitlines()
            emb_clr = int("".join(re.findall(r'[0-9]|[a-f]', str(mes_ch[0].split(" ", 3)[1]))), 16)
            emb_title = str(mes_ch[0].split(" ", 3)[2])
            emb_desc = "\n".join(mes_ch[1:])
            embed = nextcord.Embed(title=emb_title, description=emb_desc, color=emb_clr)
            await ctx.send(embed=embed)
            return
        except BaseException as err:
            await ctx.message.reply(embed=eh.eh(err))
            return


def setup(bot):
    bot.add_cog(embed(bot))