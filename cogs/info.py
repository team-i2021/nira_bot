from discord.ext import commands
import discord

import sys
sys.path.append('../')
from util import admin_check, n_fc, eh
import util.help_command as help_command

#インフォ系

class info(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def info(self, ctx: commands.Context):
        embed = discord.Embed(title="にらBOTについて", description="にらBOTは、かの有名なARK廃人の「にら」を元ネタとする、多機能DiscordBOTです！", color=0x00ff00)
        embed.add_field(name="ニラは繊細！", value="にらBOT(ってかにら君)は、とっても繊細です！\nコマンドなどを沢山送ったりすると、落ちちゃうかもしれません！\n丁寧に扱ってください！", inline=False)
        embed.add_field(name="音声再生について", value="`n!join`及び`n!play [URL]`コマンドを使用した音楽再生は、大体サーバーのスペックの問題で全然再生出来ません。まぁ気にしないでね！", inline=False)
        embed.add_field(name="詳しくは...", value="[こちら](https://nattyan-tv.github.io/nira_web/index.html)からにらBOTの詳細をご確認いただけます！どうぞご覧ください！", inline=False)
        embed.add_field(name="困ったり暇だったら...", value="[ここ](https://discord.gg/awfFpCYTcP)から謎な雑談鯖に入れるよ！", inline=False)
        if ctx.message.author.id in n_fc.py_admin:
            embed.add_field(name="ってかお前って...", value="開発者だよなお前...\n\n[メインレポジトリ](https://github.com/nattyan-tv/nira_bot) / [ウェブページレポジトリ](https://github.com/nattyan-tv/)")
        await ctx.message.reply(embed=embed)
        return
    
    @commands.command()
    async def help(self, ctx: commands.Context):
        embed = discord.Embed(title="にらBOT HELP", description="```n!help```", color=0x00ff00)
        embed.set_author(name="製作者：なつ", url="https://twitter.com/nattyan_tv", icon_url="https://pbs.twimg.com/profile_images/1388437778292113411/pBiEOtHL_400x400.jpg")
        embed.add_field(name="コマンド一覧ページ", value="[こちら](https://nattyan-tv.github.io/nira_web/index.html)", inline=False)
        await ctx.reply(embed=embed)

def setup(bot):
    bot.add_cog(info(bot))