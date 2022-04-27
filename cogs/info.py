from nextcord.ext import commands
import nextcord
from nextcord import Interaction, SlashOption, ChannelType

import sys
sys.path.append('../')
from util import admin_check, n_fc, eh
import importlib
import util.help_command as hc


#インフォ系

CTX = 0
SLASH = 1

ManageServer, ManageUser, Amuse, ServerStatus, Embed, Reaction, VoiceClient, BotUtility, ChannelTopic = range(1,10)



class HelpSelect(nextcord.ui.Select):
    def __init__(self, opt = 0):

        if opt == 0:
            options = [
                nextcord.SelectOption(label='サーバー管理/便利', value=ManageServer),
                nextcord.SelectOption(label='ユーザー', value=ManageUser),
                nextcord.SelectOption(label='娯楽', value=Amuse),
                nextcord.SelectOption(label='サーバーステータス', value=ServerStatus),
                nextcord.SelectOption(label='Embed', value=Embed),
                nextcord.SelectOption(label='にらの反応系', value=Reaction),
                nextcord.SelectOption(label='VC系', value=VoiceClient),
                nextcord.SelectOption(label='にらBOT全般', value=BotUtility),
                nextcord.SelectOption(label='チャンネルトピック', value=ChannelTopic),
            ]
        elif opt == ManageServer or int(str(opt)[0]) == ManageUser:
            options = [
                nextcord.SelectOption(label='ジャンル選択に戻る...', value=0),
                nextcord.SelectOption(label='加入/離脱者情報表示', description="n!ui", value=11),
                nextcord.SelectOption(label='ウェルカムメッセージ送信', description="n!welcome" ,value=12),
                nextcord.SelectOption(label='サーバー加入時 自動ロール付与', description="n!autorole", value=13),
                nextcord.SelectOption(label='ボタンでロールを付与するパネル', description="n!rolepanel", value=14),
                nextcord.SelectOption(label='荒らし対策機能(未完成)', description="n!mod", value=15),
                nextcord.SelectOption(label='メッセージ下部ピン止め機能(未完成)', description="n!pin", value=16),
                nextcord.SelectOption(label='サーバーを抜けてもロールを保持する', description="n!rk", value=17),
                nextcord.SelectOption(label='Bump通知機能', description="n!bump", value=18),
                nextcord.SelectOption(label='ボタンで投票するパネル(未完成)', description="n!pollpanel", value=19),
            ]
        elif opt == ManageUser or int(str(opt)[0]) == ManageUser:
            options = [
                nextcord.SelectOption(label='ジャンル選択に戻る...', value=0),
                nextcord.SelectOption(label='ユーザー情報表示', description="n!d", value=21),
                nextcord.SelectOption(label='管理者権限の有無をチェック', description="n!admin", value=22),
            ]
        elif opt == Amuse or int(str(opt)[0]) == Amuse:
            options = [
                nextcord.SelectOption(label='ジャンル選択に戻る...', value=0),
                nextcord.SelectOption(label='サイコロ', description="n!dice", value=31),
                nextcord.SelectOption(label='じゃんけん', description="n!janken", value=32),
                nextcord.SelectOption(label='占い', description="n!uranai", value=33),
                nextcord.SelectOption(label='Wordle風ゲーム', description="n!wordle", value=34),
                nextcord.SelectOption(label='しりとり風ゲーム', description="n!srtr", value=35),
            ]
        elif opt == ServerStatus or int(str(opt)[0]) == ServerStatus:
            options = [
                nextcord.SelectOption(label='ジャンル選択に戻る...', value=0),
                nextcord.SelectOption(label='Steam非公式サーバー ステータスチェック', description="n!ss", value=41),
                nextcord.SelectOption(label='Minecraftサーバー ステータスチェック(未完成)', description="n!mc", value=42),
            ]
        elif opt == Embed or int(str(opt)[0]) == Embed:
            options = [
                nextcord.SelectOption(label='ジャンル選択に戻る...', value=0),
                nextcord.SelectOption(label='Embedを送信する', description="n!embed", value=51),
            ]
        elif opt == Reaction or int(str(opt)[0]) == Reaction:
            options = [
                nextcord.SelectOption(label='ジャンル選択に戻る...', value=0),
                nextcord.SelectOption(label='にらのコマンド/Bump以外の全反応設定', description="n!ar", value=61),
                nextcord.SelectOption(label='自分で反応を追加するオートリプライ機能', description="n!er", value=62),
                nextcord.SelectOption(label='特定の言葉に反応する便乗機能', description="n!nr", value=63),
                nextcord.SelectOption(label='特定のチャンネルのメッセージをLINEに送る', description="n!line", value=64),
            ]
        elif opt == VoiceClient or int(str(opt)[0]) == VoiceClient:
            options = [
                nextcord.SelectOption(label='ジャンル選択に戻る...', value=0),
                nextcord.SelectOption(label='VCにBOTを参加させる', description="n!join", value=71),
                nextcord.SelectOption(label='VCからBOTを離脱させる', description="n!leave", value=72),
                nextcord.SelectOption(label='読み上げ機能', description="n!tts", value=73),
                nextcord.SelectOption(label='音楽を再生する', description="n!play", value=74),
                nextcord.SelectOption(label='音楽再生を全部止める', description="n!stop", value=75),
                nextcord.SelectOption(label='音楽再生を一時停止する', description="n!pause", value=76),
                nextcord.SelectOption(label='音楽再生を再開する', description="n!resume", value=77),
                nextcord.SelectOption(label='曲のリスト表示', description="n!list", value=78),
                nextcord.SelectOption(label='リストの一番後ろを消す', description="n!pop", value=79),
            ]
        elif opt == BotUtility or int(str(opt)[0]) == BotUtility:
            options = [
                nextcord.SelectOption(label='ジャンル選択に戻る...', value=0),
                nextcord.SelectOption(label='サーバーとのレイテンシを測る', description="n!ping", value=81),
                nextcord.SelectOption(label='Webページ作成', description="n!html", value=82),
                nextcord.SelectOption(label='にらBOTの情報表示', description="n!info", value=83),
                nextcord.SelectOption(label='ヘルプ表示', description="n!help", value=84),
            ]
        elif opt == ChannelTopic or int(str(opt)[0]) == ChannelTopic:
            options = [
                nextcord.SelectOption(label='ジャンル選択に戻る...', value=0),
                nextcord.SelectOption(label='そのチャンネルでにらの反応を無効化する', description="nira-off", value=91),
            ]
        
        super().__init__(placeholder='Please select help content.', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: nextcord.Interaction):
        try:
            view, value, option = nextcord.ui.View(timeout=None), int(str(self.values[0])), int(str(self.values[0])[0])
            view.add_item(HelpSelect(option))
            if value != 0:
                embed = nextcord.Embed(title=hc.helpContents[value].splitlines()[0], description="\n".join(hc.helpContents[value].splitlines()[1:]), color=0x00ff00)
            else:
                embed = nextcord.Embed(title="にらBOT HELP", description="```n!help```\nもうまったく更新してないヘルプページは[こちら](https://nira.f5.si/help.html)（非推奨）\n\n下のプルダウンからコマンド種類を選択してください。", color=0x00ff00)
            await interaction.message.edit(embed=embed, view=view)
        except BaseException as err:
            await interaction.response.send_message(f"エラーが発生しました。\n```\n{err}```\nvalue: `{self.values[0]}`/`{int(str(self.values[0])[0])}`/`{option}`", ephemeral=True)


class info_base():
    def info(self, ctx, type):
        embed = nextcord.Embed(title="にらBOTについて", description="**地味に**有能なDiscordBOT。\n主に5種類の機能があります。", color=0x00ff00)
        embed.set_author(name="製作者: なつ\n(Twitter: @nattyan_tv/GitHub: @nattyan-tv)", url="https://twitter.com/nattyan_tv", icon_url="https://pbs.twimg.com/profile_images/1498660479920603136/X-qtNrnL_400x400.jpg")
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
            embed.add_field(name="ってかお前って...", value="開発者だよな...\n開発者ならヘルプなんか見なくても何でも出来て当然だよなっ！（非常食風）\n\n[メインレポジトリ](https://github.com/nattyan-tv/nira_bot) / [ウェブページレポジトリ](https://github.com/nattyan-tv/)")
        if type == CTX:
            return ctx.reply(embed=embed)
        elif type == SLASH:
            return ctx.response.send_message(embed=embed)
    
    def help(self, ctx, command, type):
        if command == None:
            embed = nextcord.Embed(title="にらBOT HELP", description="```n!help```", color=0x00ff00)
            embed.set_author(name="製作者: なつ\n(Twitter: @nattyan_tv/GitHub: @nattyan-tv)", url="https://twitter.com/nattyan_tv", icon_url="https://pbs.twimg.com/profile_images/1498660479920603136/X-qtNrnL_400x400.jpg")
            embed.add_field(name="なんだい？僕に用かな？", value="`n!help [目的のコマンド]`と送信すると、そのコマンドの簡易ヘルプが見れるよ。", inline=False)
            embed.add_field(name="（旧互換性を保つためのやつ）", value="ずっと更新してないヘルプページは[こちら](https://nira.f5.si/help.html)", inline=False)
            if type == CTX:
                return ctx.reply(embed=embed)
            elif type == SLASH:
                return ctx.response.send_message(embed=embed)
        if command[1] not in [i.name for i in list(self.bot.commands)]:
            if type == CTX:
                return ctx.reply(f"そのコマンドは存在しないようです。")
            elif type == SLASH:
                return ctx.response.send_message("そのコマンドは存在しないようです。")
        embed = nextcord.Embed(title=f"`n!{command[1]}`", description="コマンドヘルプ", color=0x00ff00)
        for i in range(len(list(self.bot.commands))):
            if list(self.bot.commands)[i].name == command[1]:
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
        await info_base.help(self, Interaction, command, SLASH)
    
    @commands.command(name="help", help="""\
にらBOT又はコマンドのヘルプを表示します。
普通に`n!help`とだけすると、にらBOTのヘルプが表示されます。
`n!help`の後にヘルプを見たいコマンドを入れると、そのコマンドのヘルプを表示できます。
例:`n!help info`
一部のコマンドは、長すぎたり、見にくかったり、難しかったりするため、ヘルプページへのリンクを表示するだけってのもあります。

なお、ヘルプページは[こちら](https://nira.f5.si/help.html)にあります。""")
    async def help(self, ctx: commands.Context):
        command = ctx.message.content.split(" ",1)
        if len(command) == 1:
            view = nextcord.ui.View(timeout=None)
            view.add_item(HelpSelect(0))
            embed = nextcord.Embed(title="にらBOT HELP", description="```n!help```\nもうまったく更新してないヘルプページは[こちら](https://nira.f5.si/help.html)（非推奨）\n\n下のプルダウンからコマンド種類を選択してください。", color=0x00ff00)
            await ctx.send(embed=embed, view=view)
        else:
            await info_base.help(self, ctx, command, CTX)


def setup(bot):
    importlib.reload(hc)
    bot.add_cog(info(bot))
