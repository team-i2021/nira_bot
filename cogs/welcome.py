import logging
import traceback

import nextcord
from nextcord import Interaction, SlashOption
from nextcord.ext import commands

from motor import motor_asyncio

from util import admin_check, n_fc, database
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

async def editSetting(collection: motor_asyncio.AsyncIOMotorCollection, setting_type: int | None = None, guild_id: int | None = None, channel_id: int | None = None, value_type: str | int | None = None, value: str | None = None) -> int:
    """Editとか書いてるけど別にEditだけじゃないですべいび"""
    if setting_type == SET:
        await collection.update_one({"guild_id": str(guild_id), "channel_id": str(channel_id), "value_type": VALUE_TYPE[value_type]}, {"$set": {"message": value} }, upsert=True)
        return 0
    elif setting_type == DEL:
        await collection.delete_one({"guild_id": str(guild_id), "channel_id": str(channel_id), "value_type": VALUE_TYPE[value_type]})
        return 0
        #if guild_id not in WelcomeMessage.value:
        #    return 1
        #elif channel_id not in WelcomeMessage.value[guild_id]:
        #    return 2
        #WelcomeMessage.value[guild_id][channel_id][VALUE_TYPE[value_type]] = None
        #if list(WelcomeMessage.value[guild_id][channel_id]) == [None, None]:
        #    del WelcomeMessage.value[guild_id][channel_id]
        #    if len(WelcomeMessage.value[guild_id].keys()) == 0:
        #        WelcomeMessage.value[guild_id]
        #return 0
    elif setting_type == STATUS:
        result = await collection.find_one({"guild_id": str(guild_id), "channel_id": str(channel_id), "value_type": VALUE_TYPE[value_type]})
        if result is None:
            return 2
        return result["message"]


class WelcomeMaker(nextcord.ui.Modal):
    def __init__(self, message_type: str, collection):
        super().__init__(
            "Welcome Message Manage",
            timeout=None,
        )

        self.message_type = message_type
        self.collection = collection

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
            await editSetting(self.collection, SET, interaction.guild.id, interaction.channel.id, self.message_type, self.main_content.value)
            await interaction.followup.send(embed=nextcord.Embed(title=f"{self.message_type}メッセージ表示", description=self.main_content.value, color=0x00ff00), ephemeral=True)
            return
        except Exception as err:
            await interaction.followup.send("コマンド実行時にエラーが発生しました。", embed=nextcord.Embed(title=f"An error has occurred during `/welcome set [join/leave]`", description=f"```py\n{err}```\n```py\n{traceback.format_exc()}```", color=0xff0000), ephemeral=True)
            return


class Welcome(commands.Cog):
    def __init__(self, bot: NIRA, **kwargs):
        self.bot = bot
        self.collection = self.bot.database["welcome_message"]

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
    async def welcome(self, ctx: commands.Context, command: str = "", message: str = ""):
        if not admin_check.admin_check(ctx.guild, ctx.author):
            await ctx.reply(f"・Welcomeメッセージコマンド\nエラー:権限がありません。")
            return
        if command == "":
            await ctx.reply(f"・Welcomeメッセージコマンド\nエラー:引数が少ないです。\n`{self.bot.command_prefix}welcome [join/leave] [メッセージ本文]`")
            return
        if command != "join" and command != "leave":
            await ctx.reply(f"・Welcomeメッセージコマンド\nエラー:第2引数の値が不正です。\n`join`または`leave`を指定しなければなりません。\n（オフにする場合は`{ctx.prefix}[join/leave] off`としてください）")
            return
        if message == "off":
            result = await editSetting(self.collection, DEL, ctx.guild.id, ctx.channel.id, command)
            if result == 1:
                embed = nextcord.Embed(title=MESSAGES[0], description=MESSAGES[1], color=0xff0000)
            elif result == 2:
                embed = nextcord.Embed(title=MESSAGES[0], description=MESSAGES[2], color=0xff0000)
            else:
                embed = nextcord.Embed(title=MESSAGES[0], description=f"このチャンネルの{command}のメッセージを削除しました。", color=0x00ff00)
            await ctx.reply(embed=embed)
            return
        else:
            await editSetting(self.collection, SET, ctx.guild.id, ctx.channel.id, command, message)
            await ctx.reply(embed=nextcord.Embed(title=f"Welcomeメッセージ設定: `{command}`", description=message, color=0x00ff00))
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
        await interaction.response.send_modal(WelcomeMaker(MessageType, self.collection))

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
        await interaction.response.defer(ephemeral=True)
        try:
            result = await editSetting(self.collection, DEL, interaction.guild.id, interaction.channel.id, MessageType)
            if result == 1:
                embed = nextcord.Embed(title=MESSAGES[0], description=MESSAGES[1], color=0xff0000)
            elif result == 2:
                embed = nextcord.Embed(title=MESSAGES[0], description=MESSAGES[2], color=0xff0000)
            else:
                embed = nextcord.Embed(title=MESSAGES[0], description=f"このチャンネルの{MessageType}のメッセージを削除しました。", color=0x00ff00)
            await interaction.followup.send(embed=embed)
            return
        except Exception as err:
            await interaction.followup.send("コマンド実行時にエラーが発生しました。", embed=nextcord.Embed(title=f"An error has occurred during `/welcome del`", description=f"```py\n{err}```\n```py\n{traceback.format_exc()}```", color=0xff0000))
            return

    @welcome_slash.subcommand(name="status", description="Status of WelcomeMessage", description_localizations={"ja": "サーバー加入/離脱時のメッセージ設定を表示します"})
    async def status_slash(
            self,
            interaction: Interaction
        ):
        await interaction.response.defer(ephemeral=True)
        try:
            embed = nextcord.Embed(title=MESSAGES[0], description=f"{interaction.guild.name}/<#{interaction.channel.id}>", color=0x00ff00)
            result1 = await editSetting(self.collection, STATUS, interaction.guild.id, interaction.channel.id, "join")
            result2 = await editSetting(self.collection, STATUS, interaction.guild.id, interaction.channel.id, "leave")
            embed.add_field(name="joinメッセージ", value=("設定されていません。" if result1 == 2 else result1), inline=False)
            embed.add_field(name="leaveメッセージ", value=("設定されていません。" if result2 == 2 else result2), inline=False)
            await interaction.send(embed=embed)
        except Exception as err:
            logging.error(err)
            await interaction.followup.send("コマンド実行時にエラーが発生しました。", embed=nextcord.Embed(title=f"An error has occurred during `/welcome status`", description=f"```py\n{err}```\n```py\n{traceback.format_exc()}```", color=0xff0000))
            return

    @commands.Cog.listener()
    async def on_member_join(self, member: nextcord.Member):
        result = await self.collection.find({"guild_id": str(member.guild.id), "value_type": 0}).to_list(length=None)
        if len(result) == 0:
            return
        for item in result:
            channel = item["channel_id"]
            CHANNEL = member.guild.get_channel(channel)
            if CHANNEL is None:
                try:
                    CHANNEL = await member.guild.fetch_channel(channel)
                except Exception as err:
                    logging.info(f"join:{member.guild.id}に{channel}というチャンネルが見つかりませんでした。\n{err}\nSkipped.")
                    continue
            message = item["message"]
            message = message.replace("%name%", member.name)
            message = message.replace("%count%", str(len(member.guild.members)))
            message = message.replace("%ment%", member.mention)
            await CHANNEL.send(message)
            return

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        result = await self.collection.find({"guild_id": str(member.guild.id), "value_type": 1}).to_list(length=None)
        if len(result) == 0:
            return
        for item in result:
            channel = item["channel_id"]
            CHANNEL = member.guild.get_channel(channel)
            if CHANNEL is None:
                try:
                    CHANNEL = await member.guild.fetch_channel(channel)
                except Exception as err:
                    logging.info(f"join:{member.guild.id}に{channel}というチャンネルが見つかりませんでした。\n{err}\nSkipped.")
                    continue
            message = item["message"]
            message = message.replace("%name%", member.name)
            message = message.replace("%count%", str(len(member.guild.members)))
            message = message.replace("%ment%", member.mention)
            await CHANNEL.send(message)
            return


def setup(bot, **kwargs):
    bot.add_cog(Welcome(bot, **kwargs))
