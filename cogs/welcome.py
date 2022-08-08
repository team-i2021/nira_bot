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

class WelcomeMessage:
    name = "welcome_message"
    value = {}
    default = {}
    value_type = database.CHANNEL_VALUE


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
            if interaction.guild.id not in WelcomeMessage.value:
                WelcomeMessage.value[interaction.guild.id] = {interaction.channel.id: (self.message_type, self.main_content.value)}
            else:
                WelcomeMessage.value[interaction.guild.id][interaction.channel.id] = (self.message_type, self.main_content.value)
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
            if ctx.guild.id in WelcomeMessage.value:
                if args[1] in WelcomeMessage.value[ctx.guild.id]:
                    del WelcomeMessage.value[ctx.guid.id][args[1]]
                    await database.default_push(self.client, WelcomeMessage)
                    await ctx.reply(f"<#{ctx.channel.id}>の{args[1]}メッセージを削除しました。")
                else:
                    await ctx.reply(f"・Welcomeメッセージコマンド\n{args[1]}メッセージは<#{ctx.channel.id}>には設定されていません。")
            else:
                await ctx.reply(f"・Welcomeメッセージコマンド\n`{ctx.guild.name}`には設定されていません。")
            return
        if ctx.guild.id not in WelcomeMessage.value:
            WelcomeMessage.value[ctx.guild.id] = {ctx.channel.id: (args[1], args[2])}
        else:
            WelcomeMessage.value[ctx.guild.id][ctx.channel.id] = (args[1], args[2])
        await database.default_push(self.client, WelcomeMessage)
        await ctx.reply(embed=nextcord.Embed(title=f"Welcomeメッセージ設定: `{args[1]}`", description=args[2], color=0x00ff00))
        return

    @nextcord.slash_command(name="welcome", description="誰かがサーバーに加入/離脱した時にメッセージを送信します。", guild_ids=n_fc.GUILD_IDS)
    async def welcome_slash(self, interaction: Interaction):
        pass

    @welcome_slash.subcommand(name="set", description="サーバー加入/離脱時のメッセージを指定します")
    async def set_slash(
        self,
        interaction: Interaction,
        MessageType: str = SlashOption(
            name="message_type",
            description="サーバー参加時か離脱時かを選択してください",
            required=True,
            choices={"参加時": "join", "離脱時": "leave"}
        )
    ):
        await interaction.response.send_modal(WelcomeMaker(MessageType, self.client))

    @welcome_slash.subcommand(name="del", description="サーバー加入/離脱時のメッセージ設定を削除します")
    async def del_slash(
        self,
        interaction: Interaction
    ):
        await interaction.response.defer()
        try:
            if interaction.guild.id in WelcomeMessage.value:
                if interaction.channel.id in WelcomeMessage.value[interaction.guild.id]:
                    del WelcomeMessage.value[interaction.guild.id][interaction.channel.id]
                    await database.default_push(self.client, WelcomeMessage)
                    await interaction.followup.send(embed=nextcord.Embed(title=f"Welcomeメッセージ表示", description=f"・成功\n設定を削除しました。", color=0x00ff00))
                else:
                    await interaction.followup.send(embed=nextcord.Embed(title=f"Welcomeメッセージ表示", description=f"このチャンネルにはWelcomeメッセージ表示が設定されていません。", color=0xff0000), ephemeral=True)
            else:
                await interaction.followup.send(embed=nextcord.Embed(title=f"Welcomeメッセージ表示", description=f"このサーバーにはWelcomeメッセージ表示が設定されていません。", color=0xff0000), ephemeral=True)
            return
        except Exception as err:
            await interaction.followup.send("コマンド実行時にエラーが発生しました。", embed=nextcord.Embed(title=f"An error has occurred during `/welcome del`", description=f"```py\n{err}```\n```py\n{traceback.format_exc()}```", color=0xff0000))
            return

    @welcome_slash.subcommand(name="status", description="サーバー加入/離脱時のメッセージ設定を表示します")
    async def status_slash(
        self,
        interaction: Interaction
    ):
        await interaction.response.defer()
        try:
            if interaction.guild.id in WelcomeMessage.value:
                if interaction.channel.id in WelcomeMessage.value[interaction.guild.id]:
                    await interaction.followup.send(embed=nextcord.Embed(title=f"Welcomeメッセージ表示: `{WelcomeMessage.value[interaction.guild.id][interaction.channel.id][0]}`", description=WelcomeMessage.value[interaction.guild.id][interaction.channel.id][1], color=0x00ff00))
                else:
                    await interaction.followup.send(embed=nextcord.Embed(title=f"Welcomeメッセージ表示", description=f"このサーバーには参加時のメッセージ表示が設定されていません。", color=0xff0000))
            else:
                await interaction.followup.send(embed=nextcord.Embed(title=f"Welcomeメッセージ表示", description="このチャンネルには参加時のメッセージ表示が設定されていません。", color=0x00ff00))
        except Exception as err:
            logging.error(err)
            await interaction.followup.send("コマンド実行時にエラーが発生しました。", embed=nextcord.Embed(title=f"An error has occurred during `/welcome status`", description=f"```py\n{err}```\n```py\n{traceback.format_exc()}```", color=0xff0000))
            return

    @commands.Cog.listener()
    async def on_member_join(self, member: nextcord.Member):
        if member.guild.id not in WelcomeMessage.value:
            return
        for channel in WelcomeMessage.value[member.guild.id].keys():
            if WelcomeMessage.value[member.guild.id][channel][0] != "join":
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
            if WelcomeMessage.value[member.guild.id][channel][0] != "leave":
                continue
            try:
                CHANNEL = member.guild.get_channel(channel)
            except Exception as err:
                logging.error(err)
                continue
            if CHANNEL is None:
                logging.info(f"leave:{member.guild.id}に{channel}というチャンネルが見つかりませんでした。Skiped.")
                continue
            message = WelcomeMessage.value[member.guild.id][CHANNEL.id][0]
            message = message.replace("%name%", member.name)
            message = message.replace("%count%", str(len(member.guild.members)))
            message = message.replace("%ment%", member.mention)
            await CHANNEL.send(message)
            return


def setup(bot, **kwargs):
    bot.add_cog(Welcome(bot, **kwargs))
