from nextcord.ext import commands
import nextcord
from nextcord import Interaction, SlashOption, ChannelType

import sys
sys.path.append('../')
from util import admin_check, n_fc, eh
import util.help_command as help_command

#インフォ系

CTX = 0
SLASH = 1

class info_base():
    def info(self, ctx, type):
        embed = nextcord.Embed(title="にらBOTについて", description="**地味に**有能なDiscordBOT。\n主に5種類の機能があります。", color=0x00ff00)
        embed.add_field(name="・娯楽系", value="じゃんけん、しりとりで遊べたり、サイコロを振ることが出来たり、占いをすることが出来ます。", inline=False)
        embed.add_field(name="・音楽系", value="VCでYouTubeやniconicoの音楽を流すことが出来ます。", inline=False)
        embed.add_field(name="・反応系", value="「にら」に反応します。あとは、指定したトリガーが送信されたときに指定したメッセージを送信することが出来ます。あとは、Discordで送信されたメッセージをLINEに送信することが出来ます（多分）。", inline=False)
        embed.add_field(name="・ユーザー情報系", value="Discordサーバーに誰かが入った際に、そのユーザーの名前やアイコン、アカウントの作成日を指定したチャンネルに送信することが出来ます（荒らし対策）。また、ロールキーパー（一度抜けてから再度入った際に以前のロールを再付与する機能）もあります。", inline=False)
        embed.add_field(name="・サーバーステータス系", value="SteamDedicatedサーバーゲームのステータスを表示することが出来ます。\nサーバーステータスとは、「今サーバーがオンラインか」「今何人いるか」「今誰が、どれだけの時間いるか」というような情報です。\n例えば、ARKとか7DaysToDieとかなんか色々...[対応ゲーム一覧](https://developer.valvesoftware.com/wiki/Dedicated_Servers_List)\nまた、Minecraftのサーバーステータス表示にもそのうち対応させる予定です。（1000年以内に）", inline=False)
        embed.add_field(name="困ったり暇だったら...", value="[ここ](https://discord.gg/awfFpCYTcP)から謎な雑談鯖に入れるよ！", inline=False)
        if ctx.author.id in n_fc.py_admin:
            embed.add_field(name="ってかお前って...", value="開発者だよなお前...\n\n[メインレポジトリ](https://github.com/nattyan-tv/nira_bot) / [ウェブページレポジトリ](https://github.com/nattyan-tv/)")
        if type == CTX:
            return ctx.reply(embed=embed)
        elif type == SLASH:
            return ctx.response.send_message(embed=embed)
    
    def help(self, ctx, type):
        embed = nextcord.Embed(title="にらBOT HELP", description="```n!help```", color=0x00ff00)
        embed.set_author(name="製作者:`なつ`", url="https://twitter.com/nattyan_tv", icon_url="https://pbs.twimg.com/profile_images/1388437778292113411/pBiEOtHL_400x400.jpg")
        embed.add_field(name="コマンド一覧ページ", value="[こちら](https://nattyan-tv.github.io/nira_web/index.html)", inline=False)
        if type == CTX:
            return ctx.reply(embed=embed)
        elif type == SLASH:
            return ctx.response.send_message(embed=embed)

class info(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @nextcord.slash_command(name="slashtest",description="テストです。")
    async def test_slash(self, interaction: Interaction):
        await interaction.response.send_message("test")

    @nextcord.slash_command(name="info", description="にらBOTの情報を表示します。")
    async def slashcommand_info(self, interaction: Interaction):
        await info_base.info(self, Interaction, SLASH)
        return

    @commands.command()
    async def info(self, ctx: commands.Context):
        await info_base.info(self, ctx, CTX)
        return
    
    @nextcord.slash_command(name="help", description="にらBOTのヘルプを表示します。")
    async def slashcommand_help(self, Interaction: Interaction):
        await info_base.help(self, Interaction, SLASH)
    
    @commands.command()
    async def help(self, ctx: commands.Context):
        await info_base.help(self, ctx, CTX)

def setup(bot):
    bot.add_cog(info(bot))
