import asyncio
import logging
import os
import sys
import traceback

import HTTP_db
import nextcord
from nextcord import Interaction, SlashOption, ChannelType
from nextcord.ext import commands

from util import admin_check, n_fc, eh, database
from util.nira import NIRA

# join message system

SET, DEL, STATUS = [0, 1, 2]
VALUE_TYPE = {"join": 0, 0: 0, "leave": 1, 1: 1}
MESSAGES = [
    "Welcomeメッセージ",
    "このサーバーにはWelcomeメッセージは設定されていません。",
    "このチャンネルにはWelcomeメッセージは設定されていません。",
]

class WelcomeMessage:
    name = "welcome_message"
    value = {}
    default = {}
    value_type = database.CHANNEL_VALUE

def editSetting(setting_type: int | None = None, guild_id: int | None = None, channel_id: int | None = None, value_type: str | int | None = None, value: str | None = None) -> int:
    if setting_type == SET:
        if guild_id not in WelcomeMessage.value:
            WelcomeMessage.value[guild_id] = {channel_id: (None, None) }
        elif channel_id not in WelcomeMessage.value[guild_id]:
            WelcomeMessage.value[guild_id][channel_id] = (None, None)
        WelcomeMessage.value[guild_id][channel_id][VALUE_TYPE[value_type]] = value
        return 0
    elif setting_type == DEL:
        if guild_id not in WelcomeMessage.value:
            return 1
        elif channel_id not in WelcomeMessage.value[guild_id]:
            return 2
        WelcomeMessage.value[guild_id][channel_id][VALUE_TYPE[value_type]] = None
        if list(WelcomeMessage.value[guild_id][channel_id]) == [None, None]:
            del WelcomeMessage.value[guild_id][channel_id]
            if len(WelcomeMessage.value[guild_id].keys()) == 0:
                WelcomeMessage.value[guild_id]
        return 0
    elif setting_type == STATUS:
        if guild_id not in WelcomeMessage.value:
            return 1
        elif channel_id not in WelcomeMessage.value[guild_id]:
            return 2
        return WelcomeMessage.value[guild_id][channel_id][VALUE_TYPE[value_type]]


class WelcomeMaker(nextcord.ui.Modal):
    def __init__(self, message_type: str, client: HTTP_db.Client):
        super().__init__(
            "Welcome Message Manage",
            timeout=None,
        )

        self.message_type = message_type
        self.client = client

        self.main_content = nextcord.ui.TextInput(
            label="本文",
            style=nextcord.TextInputStyle.paragraph,
            placeholder="ようこそ！%ment%！%count%人目のお客様だ！\n%name%さんをこれからよろしくね！",
            required=True,
        )
        self.add_item(self.main_content)

    async def callback(self, interaction: nextcord.Interaction) -> None:
        try:
            await interaction.response.defer(ephemeral=True)
            editSetting(SET, interaction.guild.id, interaction.channel.id, self.message_type, self.main_content.value)
            await database.default_push(self.client, WelcomeMessage)
            await interaction.followup.send(embed=nextcord.Embed(title=f"{self.message_type}メッセージ表示", description=self.main_content.value, color=0x00ff00), ephemeral=True)
            return
        except Exception as err:
            await interaction.followup.send("コマンド実行時にエラーが発生しました。", embed=nextcord.Embed(title=f"An error has occurred during `/welcome set [join/leave]`", description=f"```py\n{err}```\n```py\n{traceback.format_exc()}```", color=0xff0000), ephemeral=True)
            return


class Welcome(commands.Cog):
    def __init__(self, bot: NIRA, **kwargs):
        self.bot = bot
        asyncio.ensure_future(database.default_pull(self.bot.client, WelcomeMessage))

    @commands.command(name="welcome", aliases=("youkoso", "goodbye", "ようこそ", "Welcome"), help="""\
ユーザーが加入/離脱したときに、特定のメッセージをこのチャンネルに送信するようにします。
書き方: `n!welcome [join/leave]` `[メッセージ]`
(メッセージは複数行可能です。)

メッセージ内には`%name%`/`%count%`/`%ment%`と入れることで、それぞれ`ユーザー名`/`ユーザー数`/`メンション`に置き換わります。

・例
```
n!welcome join %name%さんこんちゃ！！！！！
```

```
n!welcome leave %name%さんばいばい！！！
```

メッセージの部分に`off`と入力すると、設定を削除します。

・例
```
n!welcome join off
```

```
n!welcome leave off
```
""")
    async def welcome(self, ctx: commands.Context):
        if not admin_check.admin_check(ctx.guild, ctx.author):
            await ctx.reply("・Welcomeメッセージコマンド\nエラー:権限がありません。")
            return
        args = ctx.message.content.split(" ", 2)
        if len(args) != 3:
            await ctx.reply(f"・Welcomeメッセージコマンド\nエラー:引数が少ないです。\n`{self.bot.command_prefix}welcome [join/leave] [メッセージ本文]`")
            return
        if args[1] != "join" and args[1] != "leave":
            await ctx.reply(f"・Welcomeメッセージコマンド\nエラー:第2引数の値が不正です。\n`join`または`leave`を指定しなければなりません。")
            return
        if args[2] == "off":
            result = editSetting(DEL, ctx.guild.id, ctx.channel.id, args[1],)
            if result == 1:
                embed = nextcord.Embed(title=MESSAGES[0], description=MESSAGES[1], color=0xff0000)
            elif result == 2:
                embed = nextcord.Embed(title=MESSAGES[0], description=MESSAGES[2], color=0xff0000)
            else:
                embed = nextcord.Embed(title=MESSAGES[0], description=f"このチャンネルの{args[1]}のメッセージを削除しました。", color=0x00ff00)
            await ctx.reply(embed=embed)
            return
        else:
            editSetting(SET, ctx.guild.id, ctx.channel.id, args[1], args[2])
            await database.default_push(self.bot.client, WelcomeMessage)
            await ctx.reply(embed=nextcord.Embed(title=f"Welcomeメッセージ設定: `{args[1]}`", description=args[2], color=0x00ff00))
            return

    @nextcord.slash_command(name="welcome", description="WelcomeMessage command", guild_ids=n_fc.GUILD_IDS)
    async def welcome_slash(self, interaction: Interaction):
        pass

    @welcome_slash.subcommand(name="set", description="Set WelcomeMessage", description_localizations={"ja": "ウェルカムメッセージを設定する"})
    async def set_slash(
        self,
        interaction: Interaction,
        MessageType: str = SlashOption(
            name="message_type",
            name_localizations={"ja": "メッセージの種類"},
            description="Select the type of message to set",
            description_localizations={nextcord.Locale.ja: "サーバー参加時か離脱時かを選択してください"},
            required=True,
            choices={"参加時": "join", "離脱時": "leave"}
        )
    ):
        await interaction.response.send_modal(WelcomeMaker(MessageType, self.bot.client))

    @welcome_slash.subcommand(name="del", description="Unset WelcomeMessage", description_localizations={"ja": "ウェルカムメッセージの設定を解除する"})
    async def del_slash(
        self,
        interaction: Interaction,
        MessageType: str = SlashOption(
            name="message_type",
            name_localizations={"ja": "メッセージの種類"},
            description="Select the type of message to delete",
            description_localizations={nextcord.Locale.ja: "サーバー参加時か離脱時かを選択してください"},
            required=True,
            choices={"参加時": "join", "離脱時": "leave"}
        )
    ):
        await interaction.response.defer()
        try:
            result = editSetting(DEL, interaction.guild.id, interaction.channel.id, MessageType,)
            if result == 1:
                embed = nextcord.Embed(title=MESSAGES[0], description=MESSAGES[1], color=0xff0000)
            elif result == 2:
                embed = nextcord.Embed(title=MESSAGES[0], description=MESSAGES[2], color=0xff0000)
            else:
                embed = nextcord.Embed(title=MESSAGES[0], description=f"このチャンネルの{MessageType}のメッセージを削除しました。", color=0x00ff00)
            await interaction.send(embed=embed)
            return
        except Exception as err:
            await interaction.followup.send("コマンド実行時にエラーが発生しました。", embed=nextcord.Embed(title=f"An error has occurred during `/welcome del`", description=f"```py\n{err}```\n```py\n{traceback.format_exc()}```", color=0xff0000))
            return

    @welcome_slash.subcommand(name="status", description="Status of WelcomeMessage", description_localizations={"ja": "サーバー加入/離脱時のメッセージ設定を表示します"})
    async def status_slash(
        self,
        interaction: Interaction
    ):
        await interaction.response.defer()
        try:
            result1 = editSetting(STATUS, interaction.guild.id, interaction.channel.id, "join")
            result2 = editSetting(STATUS, interaction.guild.id, interaction.channel.id, "leave")
            if result1 == 4 or result2 == 4:
                embed = nextcord.Embed(title=MESSAGES[0], description=MESSAGES[1], color=0xff0000)
            elif result1 == 8 or result2 == 8:
                embed = nextcord.Embed(title=MESSAGES[0], description=MESSAGES[2], color=0xff0000)
            else:
                embed = nextcord.Embed(title=MESSAGES[0], description=f"{interaction.guid.name}/<#{interaction.channel.id}>", color=0x00ff00)
                embed.add_field(name="joinメッセージ", value=(lambda x: "設定されていません。" if x is None else x)(result1), inline=False)
                embed.add_field(name="leaveメッセージ", value=(lambda x: "設定されていません。" if x is None else x)(result2), inline=False)
            await interaction.send(embed=embed)
        except Exception as err:
            logging.error(err)
            await interaction.followup.send("コマンド実行時にエラーが発生しました。", embed=nextcord.Embed(title=f"An error has occurred during `/welcome status`", description=f"```py\n{err}```\n```py\n{traceback.format_exc()}```", color=0xff0000))
            return

    @commands.Cog.listener()
    async def on_member_join(self, member: nextcord.Member):
        if member.guild.id not in WelcomeMessage.value:
            return
        for channel in WelcomeMessage.value[member.guild.id].keys():
            if WelcomeMessage.value[member.guild.id][channel][0] is None:
                continue
            try:
                CHANNEL = member.guild.get_channel(channel)
            except Exception as err:
                logging.error(err)
                continue
            if CHANNEL is None:
                logging.info(f"join:{member.guild.id}に{channel}というチャンネルが見つかりませんでした。Skiped.")
                continue
            message = WelcomeMessage.value[member.guild.id][CHANNEL.id][0]
            message = message.replace("%name%", member.name)
            message = message.replace("%count%", str(len(member.guild.members)))
            message = message.replace("%ment%", member.mention)
            await CHANNEL.send(message)
            return

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if member.guild.id not in WelcomeMessage.value:
            return
        for channel in WelcomeMessage.value[member.guild.id].keys():
            if WelcomeMessage.value[member.guild.id][channel][1] is None:
                continue
            try:
                CHANNEL = member.guild.get_channel(channel)
            except Exception as err:
                logging.error(err)
                continue
            if CHANNEL is None:
                logging.info(f"leave:{member.guild.id}に{channel}というチャンネルが見つかりませんでした。Skiped.")
                continue
            message = WelcomeMessage.value[member.guild.id][CHANNEL.id][1]
            message = message.replace("%name%", member.name)
            message = message.replace("%count%", str(len(member.guild.members)))
            message = message.replace("%ment%", member.mention)
            await CHANNEL.send(message)
            return


def setup(bot, **kwargs):
    bot.add_cog(Welcome(bot, **kwargs))
