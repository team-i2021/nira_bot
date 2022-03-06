from nextcord.ext import commands
import nextcord
from nextcord import Interaction, SlashOption, ChannelType

import sys
sys.path.append('../')
from util import admin_check, n_fc, eh
import util.help_command as help_command
import nira_commands
#インフォ系

CTX = 0
SLASH = 1

class info_base():
    def info(self, ctx, type):
        embed = nextcord.Embed(title="にらBOTについて", description="**地味に**有能なDiscordBOT。\n主に5種類の機能があります。", color=0x00ff00)
        embed.add_field(name="・娯楽系", value="じゃんけん、しりとりで遊べたり、サイコロを振ることが出来たり、占いをすることが出来ます。", inline=False)
        embed.add_field(name="・音楽系", value="VCでYouTubeやniconicoの音楽を流すことが出来ます。", inline=False)
        embed.add_field(name="・反応系", value="""「にら」に反応します。あとは、指定したトリガーが送信されたときに指定したメッセージを送信することが出来ます。
        あとは、Discordで送信されたメッセージをLINEに送信することが出来ます（多分）。""", inline=False)
        embed.add_field(name="・ユーザー情報系", value="""Discordサーバーに誰かが入った際に、そのユーザーの名前やアイコン、アカウントの作成日を指定したチャンネルに送信することが出来ます（荒らし対策）。
        また、ロールキーパー（一度抜けてから再度入った際に以前のロールを再付与する機能）もあります。""", inline=False)
        embed.add_field(name="・サーバーステータス系", value="""SteamDedicatedサーバーゲームのステータスを表示することが出来ます。
        サーバーステータスとは、「今サーバーがオンラインか」「今何人いるか」「今誰が、どれだけの時間いるか」というような情報です。
        例えば、ARKとか7DaysToDieとかなんか色々...[対応ゲーム一覧](https://developer.valvesoftware.com/wiki/Dedicated_Servers_List)
        また、Minecraftのサーバーステータス表示にもそのうち対応させる予定です。（1000年以内に）""", inline=False)
        embed.add_field(name="困ったり暇だったら...", value="[ここ](https://discord.gg/awfFpCYTcP)から謎な雑談鯖に入れるよ！", inline=False)
        if ctx.author.id in n_fc.py_admin:
            embed.add_field(name="ってかお前って...", value="開発者だよなお前...\n\n[メインレポジトリ](https://github.com/nattyan-tv/nira_bot) / [ウェブページレポジトリ](https://github.com/nattyan-tv/)")
        if type == CTX:
            return ctx.reply(embed=embed)
        elif type == SLASH:
            return ctx.response.send_message(embed=embed)
    
    def help(self, ctx, command, type):
        if command == None:
            embed = nextcord.Embed(title="にらBOT HELP", description="```n!help```", color=0x00ff00)
            embed.set_author(name="製作者:`なつ`", url="https://twitter.com/nattyan_tv", icon_url="https://pbs.twimg.com/profile_images/1498660479920603136/X-qtNrnL_400x400.jpg")
            embed.add_field(name="コマンド一覧ページ", value="[こちら](https://nira.f5.si/help.html)", inline=False)
            if type == CTX:
                return ctx.reply(embed=embed)
            elif type == SLASH:
                return ctx.response.send_message(embed=embed)
        if command not in [i.name for i in list(self.bot.commands)]:
            if type == CTX:
                return ctx.reply("そのコマンドは存在しないようです。")
            elif type == SLASH:
                return ctx.response.send_message("そのコマンドは存在しないようです。")
        embed = nextcord.Embed(title=f"`n!{command}`", description="コマンドヘルプ", color=0x00ff00)
        for i in range(len(list(self.bot.commands))):
            if list(self.bot.commands)[i].name == command:
                if list(self.bot.commands)[i].help == None:
                    embed.add_field(name="Sorry...", value="このコマンドのヘルプは存在しないか、現在制作中です。")
                    if type == CTX:
                        return ctx.reply(embed=embed)
                    elif type == SLASH:
                        return ctx.response.send_message(embed=embed)
                embed.add_field(name=list(self.bot.commands)[i].help.splitlines()[0], value="\n".join(list(self.bot.commands)[i].help.splitlines()[1:]))
                embed.set_footer(text="nira-bot Powered by NattyanTV")
                if type == CTX:
                    return ctx.reply(embed=embed)
                elif type == SLASH:
                    return ctx.response.send_message("そのコマンドは存在しないようです。")

class info(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @nextcord.slash_command(name="slashtest",description="テストです。")
    async def test_slash(self, interaction: Interaction):
        await interaction.response.send_message("test")

    @nextcord.slash_command(name="info", description="にらBOTの情報を表示します。")
    async def slashcommand_info(self, interaction: Interaction):
        await info_base.info(self, interaction, SLASH)
        return

    @commands.command(name="info", help="""\
        にらBOTの情報を表示します。
        どのようなコマンドがあるかを大雑把に説明したり、Discordサポートサーバー、GitHubレポジトリへのリンクがあります。""")
    async def info(self, ctx: commands.Context):
        await info_base.info(self, ctx, CTX)
        return
    
    @nextcord.slash_command(name="help", description="にらBOT及び、コマンドのヘルプを表示します。")
    async def slashcommand_help(self, Interaction: Interaction, command: str):
        if command == "":
            command = None
        await info_base.help(self, Interaction, SLASH)
    
    @commands.command(name="help", help="""\
        にらBOT又はコマンドのヘルプを表示します。
        普通に`n!help`とだけすると、にらBOTの簡易ヘルプが表示されます。
        `n!help`の後にヘルプを見たいコマンドを入れると、そのコマンドのヘルプを表示できます。
        例:`n!help info`
        一部のコマンドは、長すぎたり、見にくかったり、難しかったりするため、ヘルプページへのリンクを表示するだけってのもあります。""")
    async def help(self, ctx: commands.Context):
        command = ctx.message.content[7:]
        if ctx.message.content[7:] == "":
            command = None
        await info_base.help(self, ctx, command, CTX)

def setup(bot):
    bot.add_cog(info(bot))
