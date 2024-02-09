import asyncio
from motor import motor_asyncio
from typing import Any, TypedDict

import nextcord
from nextcord import Interaction, SlashOption
from nextcord.ext import commands, application_checks, tasks

from util.nira import NIRA

class AutoEmojiSetting(TypedDict):
    """
    `AutoEmoji.autoemoji_list`に使用される、AutoEmojiの設定を表す型です。
    """
    channel_id: int
    emojis: list[str]

class AutoEmoji(commands.Cog):
    """
    AutoEmojiは、設定チャンネルにメッセージが投稿された際に、自動で絵文字リアクションを行う機能です。
    これを行うことでチャンネル運用がもしかしたら便利になるかもしれません。
    """
    def __init__(self, bot: NIRA, **kwargs: Any):
        self.bot = bot
        self.autoemoji_collection: motor_asyncio.AsyncIOMotorCollection = self.bot.database["autoemoji_setting"]
        self.autoemoji_list: list[AutoEmojiSetting] = []
        self.load_autoemoji_settings.start()

    @tasks.loop(hours=1.0)
    async def load_autoemoji_settings(self):
        """
        AutoEmojiの設定を、データベースからローカルへロードします。
        """
        self.autoemoji_list = []
        async for autoemoji in self.autoemoji_collection.find():
            self.autoemoji_list.append(autoemoji)

    @nextcord.slash_command(
        name="autoemoji",
        description="Configure autoemoji settings",
    )
    async def autoemoji_slash(self, interaction: Interaction):
        pass

    @application_checks.guild_only()
    @autoemoji_slash.subcommand(
        name="add",
        description="Add a new autoemoji",
        description_localizations={
            nextcord.Locale.ja: "新しい自動絵文字を追加します。",
        }
    )
    async def add_autoemoji_slash(
        self,
        interaction: Interaction,
        emojis: str = SlashOption(
            name="emojis",
            name_localizations={
                nextcord.Locale.ja: "絵文字",
            },
            description="Comma separated emojis to add",
            description_localizations={
                nextcord.Locale.ja: "カンマ区切りで絵文字を指定してください。",
            },
            required=True,
        )
    ):
        assert isinstance(interaction.guild, nextcord.Guild)
        assert interaction.channel is not None
        await interaction.response.defer(ephemeral=False)
        message = await interaction.followup.send(
            embed=nextcord.Embed(
                title="しばらくお待ちください...",
                description="絵文字のチェックを行っています。",
                color=self.bot.color.ATTENTION
            ),
            wait=True
        )
        emojis = emojis.replace(" ", "")
        emoji_list = emojis.split(",")
        if len(emoji_list) > 10:
            await message.edit(
                embed=nextcord.Embed(
                    title="AutoEmoji - Error",
                    description="設定できる絵文字は10個までです。",
                    color=self.bot.color.ERROR
                )
            )
            return
        for emoji in emoji_list:
            try:
                await message.add_reaction(emoji)
            except nextcord.Forbidden:
                await message.edit(
                    embed=nextcord.Embed(
                        title="AutoEmoji - Error",
                        description=(
                            f"絵文字 {emoji} (`{emoji}`)の確認時にエラーが発生しました。\n"
                            "絵文字を追加する権限がありませんでした。"
                        ),
                        color=self.bot.color.ERROR
                    )
                )
                return
            except nextcord.NotFound:
                await message.edit(
                    embed=nextcord.Embed(
                        title="AutoEmoji - Error",
                        description=(
                            f"絵文字 {emoji} (`{emoji}`)の確認時にエラーが発生しました。\n"
                            "絵文字が見つかりませんでした。"
                        ),
                        color=self.bot.color.ERROR
                    )
                )
                return
            except nextcord.InvalidArgument:
                await message.edit(
                    embed=nextcord.Embed(
                        title="AutoEmoji - Error",
                        description=(
                            f"絵文字 {emoji} (`{emoji}`)の確認時にエラーが発生しました。\n"
                            "絵文字が無効です。"
                        ),
                        color=self.bot.color.ERROR
                    )
                )
                return
            except nextcord.HTTPException as e:
                await message.edit(
                    embed=nextcord.Embed(
                        title="AutoEmoji - Error",
                        description=(
                            f"絵文字 {emoji} (`{emoji}`)の確認時にエラーが発生しました。\n"
                            "絵文字はカンマ区切りで入力されているかご確認ください。\n"
                            "または...一時的なネットワークエラーが発生している可能性があります。"
                        ),
                        color=self.bot.color.ERROR
                    )
                )
                return
        try:
            await self.autoemoji_collection.update_one(
                filter={"channel_id": interaction.channel.id},
                update={"$set": {"emojis": emoji_list}},
                upsert=True
            )
            self.autoemoji_list.append({"channel_id": interaction.channel.id, "emojis": emoji_list})
        except Exception as e:
            await message.edit(
                embed=nextcord.Embed(
                    title="AutoEmoji - Error",
                    description=f"エラーが発生しました。\n```{e}```",
                    color=self.bot.color.ERROR
                )
            )
            return
        await message.edit(
            embed=nextcord.Embed(
                title="AutoEmoji - Success",
                description=(
                    f"絵文字 {emojis} (`{emojis}`)をこのチャンネルに追加しました。\n"
                    "このチャンネルにメッセージが送信されると自動で絵文字リアクションが行われます。"
                ),
                color=self.bot.color.NORMAL
            )
        )

    @application_checks.guild_only()
    @autoemoji_slash.subcommand(
        name="del",
        description="Delete autoemoji from this channel",
        description_localizations={
            nextcord.Locale.ja: "このチャンネルの自動絵文字を削除します。",
        }
    )
    async def del_autoemoji_slash(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=False)
        assert isinstance(interaction.guild, nextcord.Guild)
        assert interaction.channel is not None
        delete_status = await self.autoemoji_collection.delete_one({"channel_id": interaction.channel.id})
        if delete_status.deleted_count == 0:
            await interaction.send(
                embed=nextcord.Embed(
                    title="AutoEmoji - Error",
                    description="このチャンネルには自動絵文字が設定されていません。",
                    color=self.bot.color.ERROR
                ),
                ephemeral=True
            )
            return
        await interaction.send(
            embed=nextcord.Embed(
                title="AutoEmoji - Success",
                description=(
                    "このチャンネルの自動絵文字を削除しました。\n"
                    "このメッセージにつく絵文字が最後の絵文字だよ..."
                ),
                color=self.bot.color.NORMAL
            ),
            ephemeral=True
        )
        for autoemoji in self.autoemoji_list:
            if autoemoji["channel_id"] == interaction.channel.id:
                self.autoemoji_list.remove(autoemoji)
                break

    @application_checks.guild_only()
    @autoemoji_slash.subcommand(
        name="list",
        description="List autoemoji settings",
        description_localizations={
            nextcord.Locale.ja: "自動絵文字の設定を表示します。",
        }
    )
    async def list_autoemoji_slash(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=False)
        assert interaction.channel is not None

        autoemoji_settings = list(filter(lambda x: x["channel_id"] == interaction.channel.id, self.autoemoji_list))
        if len(autoemoji_settings) == 0:
            await interaction.send(
                embed=nextcord.Embed(
                    title="AutoEmoji - List",
                    description="このチャンネルには自動絵文字が設定されていません。",
                    color=self.bot.color.NORMAL
                ),
                ephemeral=True
            )
            return
        autoemoji_setting = autoemoji_settings[0]
        emoji_list = autoemoji_setting["emojis"]
        await interaction.send(
            embed=nextcord.Embed(
                title="AutoEmoji - List",
                description=(
                    "このチャンネルでリアクションするように設定されている絵文字は以下の通りです。\n"
                    f"{', '.join(emoji_list)}\n"
                    f"(`{', '.join(emoji_list)}`)"
                ),
                color=self.bot.color.NORMAL
            ),
            ephemeral=True
        )

    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message):
        if not message.guild:
            return
        autoemoji_settings = list(filter(lambda x: x["channel_id"] == message.channel.id, self.autoemoji_list))
        if len(autoemoji_settings) == 0:
            return
        autoemoji_setting = autoemoji_settings[0]
        emoji_list = autoemoji_setting["emojis"]
        for emoji in emoji_list:
            try:
                await message.add_reaction(emoji)
            except nextcord.Forbidden:
                pass
            except nextcord.NotFound:
                pass
            except nextcord.InvalidArgument:
                pass
            except nextcord.HTTPException:
                pass
            await asyncio.sleep(1)

def setup(bot: NIRA, **kwargs: Any):
    bot.add_cog(AutoEmoji(bot, **kwargs))
