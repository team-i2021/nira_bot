import importlib
import logging
import sys
import traceback

import nextcord
from nextcord import Interaction, SlashOption, ChannelType
from nextcord.ext import commands

import util.help_command as hc
from util import admin_check, n_fc, eh, slash_tool

# インフォ系

CTX = 0
SLASH = 1

ManageServer, ManageUser, Amuse, ServerStatus, General, Reaction, VoiceClient, BotUtility, ChannelTopic, MessageCommand, MemberCommand = [
    f"G-{i}" for i in range(1, 12)]


class HelpSelect(nextcord.ui.Select):
    def __init__(self, prefix, opt):
        self.prefix = prefix
        if opt == "0":
            options = [
                nextcord.SelectOption(label='サーバー管理/便利', value=ManageServer),
                nextcord.SelectOption(label='ユーザー', value=ManageUser),
                nextcord.SelectOption(label='娯楽', value=Amuse),
                nextcord.SelectOption(label='サーバーステータス', value=ServerStatus),
                nextcord.SelectOption(label='汎用コマンド', value=General),
                nextcord.SelectOption(label='にらの反応系', value=Reaction),
                nextcord.SelectOption(label='VC系', value=VoiceClient),
                nextcord.SelectOption(label='にらBOT関係', value=BotUtility),
                nextcord.SelectOption(label='チャンネルトピック', value=ChannelTopic),
                nextcord.SelectOption(label='メッセージコマンド', value=MessageCommand),
                nextcord.SelectOption(label='メンバーコマンド', value=MemberCommand),
            ]
        elif opt == ManageServer:
            options = [
                nextcord.SelectOption(
                    label='ジャンル選択に戻る...',
                    value="0"
                ),
                nextcord.SelectOption(
                    label='加入/離脱者情報表示',
                    description=f"{prefix}ui",
                    value="1-1"
                ),
                nextcord.SelectOption(
                    label='ウェルカムメッセージ送信',
                    description=f"{prefix}welcome",
                    value="1-2"
                ),
                nextcord.SelectOption(
                    label='サーバー加入時 自動ロール付与',
                    description=f"{prefix}autorole",
                    value="1-3"),
                nextcord.SelectOption(
                    label='ボタンでロールを付与するパネル',
                    description=f"{prefix}rolepanel",
                    value="1-4",
                ),
                nextcord.SelectOption(
                    label='荒らし対策機能(未完成)',
                    description=f"{prefix}mod",
                    value="1-5"
                ),
                nextcord.SelectOption(
                    label='メッセージ下部ピン止め機能(未完成)',
                    description=f"{prefix}pin",
                    value="1-6"
                ),
                nextcord.SelectOption(
                    label='サーバーを抜けてもロールを保持する',
                    description=f"{prefix}rk",
                    value="1-7",
                ),
                nextcord.SelectOption(
                    label='Bump通知機能',
                    description=f"{prefix}bump",
                    value="1-8",
                ),
                nextcord.SelectOption(
                    label='ボタンで投票するパネル',
                    description=f"{prefix}pollpanel",
                    value="1-9",
                ),
                nextcord.SelectOption(
                    label='Dissoku Up通知機能',
                    description=f"{prefix}up",
                    value="1-10"
                ),
                nextcord.SelectOption(
                    label='メッセージDM機能',
                    description=f"{prefix}mesdm",
                    value="1-11"
                ),
                nextcord.SelectOption(
                    label='メッセージロール機能',
                    description=f"{prefix}mesrole",
                    value="1-12"
                ),
                nextcord.SelectOption(
                    label='下部ピン留め機能',
                    description=f"{prefix}pin",
                    value="1-13"
                ),
                nextcord.SelectOption(
                    label='リマインド機能',
                    description=f"{prefix}remind",
                    value="1-14"
                ),
            ]
        elif opt == ManageUser:
            options = [
                nextcord.SelectOption(
                    label='ジャンル選択に戻る...',
                    value="0"
                ),
                nextcord.SelectOption(
                    label='ユーザー情報表示',
                    description=f"{prefix}d",
                    value="2-1",
                ),
                nextcord.SelectOption(
                    label='管理者権限の有無をチェック',
                    description=f"{prefix}admin",
                    value="2-2",
                ),
                nextcord.SelectOption(
                    label='Invite機能',
                    description=f"{prefix}invite",
                    value="2-3",
                ),
            ]
        elif opt == Amuse:
            options = [
                nextcord.SelectOption(
                    label='ジャンル選択に戻る...',
                    value="0"
                ),
                nextcord.SelectOption(
                    label='サイコロ',
                    description=f"{prefix}dice",
                    value="3-1",
                ),
                nextcord.SelectOption(
                    label='じゃんけん',
                    description=f"{prefix}janken",
                    value="3-2",
                ),
                nextcord.SelectOption(
                    label='占い',
                    description=f"{prefix}uranai",
                    value="3-3",
                ),
                nextcord.SelectOption(
                    label='Wordle風ゲーム',
                    description=f"{prefix}wordle",
                    value="3-4",
                ),
                nextcord.SelectOption(
                    label='しりとり風ゲーム',
                    description=f"{prefix}srtr",
                    value="3-5",
                ),
            ]
        elif opt == ServerStatus:
            options = [
                nextcord.SelectOption(
                    label='ジャンル選択に戻る...',
                    value="0"
                ),
                nextcord.SelectOption(
                    label='Steam非公式サーバー ステータスチェック',
                    description=f"{prefix}ss",
                    value="4-1",
                ),
                nextcord.SelectOption(
                    label='Minecraftサーバー ステータスチェック',
                    description=f"{prefix}mc",
                    value="4-2",
                ),
            ]
        elif opt == General:
            options = [
                nextcord.SelectOption(
                    label='ジャンル選択に戻る...',
                    value="0"
                ),
                nextcord.SelectOption(
                    label='Embedを送信する',
                    description=f"{prefix}embed",
                    value="5-1",
                ),
                nextcord.SelectOption(
                    label='メッセージを翻訳する',
                    description=f"{prefix}translate",
                    value="5-2",
                ),
            ]
        elif opt == Reaction:
            options = [
                nextcord.SelectOption(
                    label='ジャンル選択に戻る...',
                    value="0"
                ),
                nextcord.SelectOption(
                    label='にらのコマンド/Bump以外の全反応設定',
                    description=f"{prefix}ar",
                    value="6-1",
                ),
                nextcord.SelectOption(
                    label='自分で反応を追加するオートリプライ機能',
                    description=f"{prefix}er",
                    value="6-2",
                ),
                nextcord.SelectOption(
                    label='特定の言葉に反応する便乗機能',
                    description=f"{prefix}nr",
                    value="6-3",
                ),
                nextcord.SelectOption(
                    label='特定のチャンネルのメッセージをLINEに送る',
                    description=f"{prefix}line",
                    value="6-4",
                ),
            ]
        elif opt == VoiceClient:
            options = [
                nextcord.SelectOption(
                    label='ジャンル選択に戻る...',
                    value="0"
                ),
                nextcord.SelectOption(
                    label='VCにBOTを参加させる',
                    description=f"{prefix}join",
                    value="7-1",
                ),
                nextcord.SelectOption(
                    label='VCからBOTを離脱させる',
                    description=f"{prefix}leave",
                    value="7-2",
                ),
                nextcord.SelectOption(
                    label='読み上げ機能',
                    description=f"{prefix}tts",
                    value="7-3",
                ),
                nextcord.SelectOption(
                    label='音楽を再生する',
                    description=f"{prefix}play",
                    value="7-4",
                ),
                nextcord.SelectOption(
                    label='音楽再生を全部止める',
                    description=f"{prefix}stop",
                    value="7-5",
                ),
                nextcord.SelectOption(
                    label='音楽再生を一時停止する',
                    description=f"{prefix}pause",
                    value="7-6",
                ),
                nextcord.SelectOption(
                    label='音楽再生を再開する',
                    description=f"{prefix}resume",
                    value="7-7",
                ),
                nextcord.SelectOption(
                    label='曲のリスト表示',
                    description=f"{prefix}list",
                    value="7-8",
                ),
                nextcord.SelectOption(
                    label='リストの一番後ろを消す',
                    description=f"{prefix}pop",
                    value="7-9",
                ),
            ]
        elif opt == BotUtility:
            options = [
                nextcord.SelectOption(
                    label='ジャンル選択に戻る...',
                    value="0"
                ),
                nextcord.SelectOption(
                    label='サーバーとのレイテンシを測る',
                    description=f"{prefix}ping",
                    value="8-1"
                ),
                nextcord.SelectOption(
                    label='Webページ作成',
                    description=f"{prefix}html",
                    value="8-2"
                ),
                nextcord.SelectOption(
                    label='にらBOTの情報表示',
                    description=f"{prefix}info",
                    value="8-3"
                ),
                nextcord.SelectOption(
                    label='ヘルプ表示',
                    description=f"{prefix}help",
                    value="8-4"
                ),
            ]
        elif opt == ChannelTopic:
            options = [
                nextcord.SelectOption(
                    label='ジャンル選択に戻る...',
                    value="0"
                ),
                nextcord.SelectOption(
                    label='チャンネルでにらの反応を無効化する',
                    description="nira-off",
                    value="9-1"
                ),
                nextcord.SelectOption(
                    label='チャンネルメッセージを自動翻訳する',
                    description="nira-tl-(en|ja|auto)",
                    value="9-2"
                ),
            ]
        elif opt == MessageCommand:
            options = [
                nextcord.SelectOption(
                    label='ジャンル選択に戻る...',
                    value="0"
                ),
                nextcord.SelectOption(
                    label='Embed取得',
                    value="10-1"
                ),
                nextcord.SelectOption(
                    label='メッセージ翻訳',
                    value="10-2"
                ),
                nextcord.SelectOption(
                    label='メッセージ読み上げ',
                    value="10-3"
                ),
                nextcord.SelectOption(
                    label='ロールパネル編集',
                    value="10-4"
                ),
                nextcord.SelectOption(
                    label='下部ピン留めする',
                    value="10-5"
                ),
            ]
        elif opt == MemberCommand:
            options = [
                nextcord.SelectOption(
                    label='ジャンル選択に戻る...',
                    value="0"
                ),
                nextcord.SelectOption(
                    label='ユーザー情報表示',
                    value="11-1"
                ),
                nextcord.SelectOption(
                    label='管理者権限チェック',
                    value="11-2"
                ),
            ]

        super().__init__(
            placeholder='Please select help content.',
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: nextcord.Interaction):
        try:
            value = self.values[0]
            view = nextcord.ui.View(timeout=None)
            view.add_item(
                HelpSelect(
                    prefix=self.prefix,
                    opt=(
                        lambda x: f"0" if x[0] == "0" else f"G-{x[1]}" if x[0] == "G" else f"G-{x[0]}"
                    )(
                        value.split("-", 1)
                    )
                )
            )
            if value != "0":
                embed = nextcord.Embed(
                    title=hc.helpContents[
                        (
                            lambda x: int(
                                value.split("-", 1)[0]
                            ) if x != "G" else "G"
                        )(
                            value.split("-", 1)[0]
                        )
                    ][
                        int(value.split("-", 1)[1])
                    ].splitlines()[0],
                    description="\n".join(
                        hc.helpContents[
                            (
                                lambda x: int(
                                    value.split("-", 1)[0]
                                ) if x != "G" else "G"
                            )(
                                value.split("-", 1)[0]
                            )
                        ][
                            int(value.split("-", 1)[1])
                        ].splitlines()[1:]),
                    color=0x00ff00
                )
            else:
                embed = nextcord.Embed(
                    title="にらBOT HELP",
                    description=f"```{self.prefix}help```\nもうまったく更新してないヘルプページは[こちら](https://nira.f5.si/help.html)（非推奨）\n\n下のプルダウンからコマンド種類を選択してください。",
                    color=0x00ff00
                )
            await interaction.message.edit(embed=embed, view=view)
            return
        except Exception:
            await interaction.response.send_message(f"エラーが発生しました。\n```\n{traceback.format_exc()}```", ephemeral=True)
            return


class info_base():
    def info(self, ctx, type):
        embed = nextcord.Embed(
            title="にらBOTについて",
            description="にらBOTです。[ニラ](https://ja.m.wikipedia.org/wiki/ニラ)（韮、韭、Allium tuberosum）は、ネギ属に属する多年草。緑黄色野菜で...って...あれ？違う？",
            color=0x00ff00
        )
        embed.set_author(
            name="製作者: なつ\n(Twitter: @nattyan_tv/GitHub: @nattyan-tv)",
            url="https://twitter.com/nattyan_tv",
            icon_url="https://nira.f5.si/nattyantv.jpg"
        )
        embed.add_field(
            name="沢山の機能",
            value=f"""\
サーバー管理にうってつけな機能から、便利な機能、暇なときに遊べる機能から、ARKやMinecraftのサーバーのステータスをチェックする機能まで...!
すべてのコマンドは`{self.bot.command_prefix}help`または`/help`とヘルプコマンドを打って確認してみてください!
さぁ、足りない部分は他のBOTが補ってくれるとは思うけど、にらBOTで完結することはにらBOTで完結させましょう!

ユーザーフレンドリーなんで、ほしい機能とかあったり、ただただ暇だったらサポートサーバー入って、どんどん言ってね!""",
            inline=False
        )
        embed.add_field(
            name="リンク集",
            value=f"""\
- BOT招待リンク
[https://nira.f5.si/invite](https://nira.f5.si/invite)

- サポートサーバー
[https://discord.gg/awfFpCYTcP](https://discord.gg/awfFpCYTcP)

- NIRA Net
[https://nira.f5.si](https://nira.f5.si)

- (一応)ホームページ
[https://sites.google.com/view/nira-bot](https://sites.google.com/view/nira-bot)""",
            inline=False
        )
        embed.add_field(
            name="GitHubレポジトリ",
            value="""\
- NIRA Bot
[https://github.com/team-i2021/nira_bot](https://github.com/team-i2021/nira_bot)

- NIRA Net
[https://github.com/team-i2021/nira_net](https://github.com/team-i2021/nira_net)""",
            inline=False
        )
        if type == CTX:
            if ctx.author.id in n_fc.py_admin:
                embed = nextcord.Embed(title="About nira-bot", description=f"""\
You are Bot administrator!

- Cogs
```
{list(dict(self.bot.cogs).keys())}```

Guilds: `{len(self.bot.guilds)}`
Users: `{len(self.bot.users)}`
VoiceClients: `{len(self.bot.voice_clients)}`
Latency: `{round(self.bot.latency*1000, 2)}ms`
""", color=0x7777ff)
            return ctx.reply(embed=embed)
        elif type == SLASH:
            if ctx.user.id in n_fc.py_admin:
                embed = nextcord.Embed(title="About nira-bot", description=f"""\
You are Bot administrator!

- Cogs
```
{list(dict(self.bot.cogs).keys())}```

Guilds: `{len(self.bot.guilds)}`
Users: `{len(self.bot.users)}`
VoiceClients: `{len(self.bot.voice_clients)}`
Latency: `{round(self.bot.latency*1000, 2)}ms`
""", color=0x7777ff)
            return ctx.response.send_message(embed=embed)

    def help(self, ctx, command, type):
        if command == None:
            view = nextcord.ui.View(timeout=None)
            view.add_item(HelpSelect("/", "0"))
            embed = nextcord.Embed(
                title="にらBOT HELP", description="```/help```\nもうまったく更新してないヘルプページは[こちら](https://nira.f5.si/help.html)（非推奨）\n\n下のプルダウンからコマンド種類を選択してください。", color=0x00ff00)
            if type == CTX:
                return ctx.reply(embed=embed, view=view)
            elif type == SLASH:
                return ctx.response.send_message(embed=embed, view=view)
        if command not in [i.name for i in list(self.bot.commands)]:
            if type == CTX:
                return ctx.reply(f"そのコマンド`{command}`は存在しないようです。")
            elif type == SLASH:
                return ctx.response.send_message(f"そのコマンド`{command}`は存在しないようです。")

        embed = nextcord.Embed(
            title=f"`{self.bot.command_prefix}{command}`", description="コマンドヘルプ", color=0x00ff00)
        for i in range(len(list(self.bot.commands))):
            if list(self.bot.commands)[i].name == command:
                if list(self.bot.commands)[i].help == None:
                    embed.add_field(name="Sorry...",
                                    value="このコマンドのヘルプは存在しないか、現在制作中です。")
                    if type == CTX:
                        return ctx.reply(embed=embed)
                    elif type == SLASH:
                        return ctx.response.send_message(embed=embed)
                embed.add_field(name=list(self.bot.commands)[i].help.splitlines()[
                                0], value="\n".join(list(self.bot.commands)[i].help.splitlines()[1:]))
                embed.set_footer(text="nira-bot Powered by NattyanTV")
                if type == CTX:
                    return ctx.reply(embed=embed, view=nextcord.ui.View(timeout=None).add_item(HelpSelect(self.bot.command_prefix, "0")))
                elif type == SLASH:
                    return ctx.response.send_message(embed=embed, view=nextcord.ui.View(timeout=None).add_item(HelpSelect("/", "0")))


class info(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @ nextcord.slash_command(name="info", description="にらBOTの情報を表示します。", guild_ids=n_fc.GUILD_IDS)
    async def info_slash(self, interaction: Interaction):
        await info_base.info(self, interaction, SLASH)
        return

    @ commands.command(name="info", help="""\
にらBOTの情報を表示します。
どのようなコマンドがあるかを大雑把に説明したり、Discordサポートサーバー、GitHubレポジトリへのリンクがあります。""")
    async def info(self, ctx: commands.Context):
        await info_base.info(self, ctx, CTX)
        return

    @ nextcord.slash_command(name="help", description="にらBOT及び、コマンドのヘルプを表示します。", guild_ids=n_fc.GUILD_IDS)
    async def help_slash(
        self,
        interaction: Interaction,
        command: str = SlashOption(
            name="command",
            description="ヘルプを表示するコマンドを指定します。",
            required=False
        )
    ):
        if command == "":
            command = None
        await info_base.help(self, interaction, command, SLASH)

    @ commands.command(name="help", help="""\
にらBOT又はコマンドのヘルプを表示します。
普通に`n!help`とだけすると、にらBOTのヘルプが表示されます。
`n!help`の後にヘルプを見たいコマンドを入れると、そのコマンドのヘルプを表示できます。
例:`n!help info`
一部のコマンドは、長すぎたり、見にくかったり、難しかったりするため、ヘルプページへのリンクを表示するだけってのもあります。

なお、ヘルプページは[こちら](https://nira.f5.si/help.html)にあります。""")
    async def help(self, ctx: commands.Context):
        command = ctx.message.content.split(" ", 1)
        if len(command) == 1:
            view = nextcord.ui.View(timeout=None)
            view.add_item(HelpSelect(prefix=self.bot.command_prefix, opt="0"))
            embed = nextcord.Embed(
                title="にらBOT HELP", description=f"```{self.bot.command_prefix}help```\nもうまったく更新してないヘルプページは[こちら](https://nira.f5.si/help.html)（非推奨）\n\n下のプルダウンからコマンド種類を選択してください。", color=0x00ff00)
            await ctx.send(embed=embed, view=view)
        else:
            await info_base.help(self, ctx, command[1], CTX)


def setup(bot):
    importlib.reload(hc)
    bot.add_cog(info(bot))
