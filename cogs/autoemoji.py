import asyncio
import logging
from motor import motor_asyncio

import nextcord
from nextcord import Interaction, SlashOption
from nextcord.ext import commands, application_checks, tasks

from util.nira import NIRA


class AutoEmoji(commands.Cog):
    """
    AutoEmojiは、設定チャンネルにメッセージが投稿された際に、自動で絵文字リアクションを行う機能です。
    これを行うことでチャンネル運用がもしかしたら便利になるかもしれません。
    """

    def __init__(self, bot: NIRA):
        self.bot = bot
        self.autoemoji_collection: motor_asyncio.AsyncIOMotorCollection = self.bot.database["autoemoji_setting"]
        self.autoemoji_cache: dict[int, list[str]] = {}
        self.load_autoemoji_settings.start()

    @tasks.loop(hours=1.0)
    async def load_autoemoji_settings(self):
        """
        AutoEmojiの設定を、データベースからローカルへロードします。
        """
        self.autoemoji_cache = {}
        async for autoemoji in self.autoemoji_collection.find():
            self.autoemoji_cache[int(autoemoji["channel_id"])] = autoemoji["emojis"]

    @nextcord.slash_command(
        name="autoemoji",
        description="Configure autoemoji settings",
    )
    async def autoemoji_slash(self, interaction: Interaction):
        pass

    @application_checks.guild_only()
    @autoemoji_slash.subcommand(
        name="set",
        description="Set autoemoji to this channel",
        description_localizations={
            nextcord.Locale.ja: "このチャンネルに自動絵文字を設定します。",
        },
    )
    async def set_autoemoji_slash(
        self,
        interaction: Interaction,
        emojis: str = SlashOption(
            name="emojis",
            name_localizations={
                nextcord.Locale.ja: "絵文字",
            },
            description="Comma separated emojis to set",
            description_localizations={
                nextcord.Locale.ja: "設定したい絵文字をカンマ区切りで指定してください。",
            },
            required=True,
        ),
    ):
        assert interaction.guild is not None
        assert interaction.channel is not None

        await interaction.response.defer(ephemeral=False)

        exist_status = await self.autoemoji_collection.find_one({"channel_id": interaction.channel.id})
        if exist_status is not None:
            await interaction.send(
                embed=nextcord.Embed(
                    title="AutoEmoji - Error",
                    description=(
                        "このチャンネルには既に自動絵文字が設定されています。\n"
                        "削除するには`/autoemoji del`を使用してください。"
                    ),
                    color=self.bot.color.ERROR,
                )
            )
            return

        message = await interaction.followup.send(
            embed=nextcord.Embed(
                title="しばらくお待ちください...",
                description="絵文字のチェックを行っています。",
                color=self.bot.color.ATTENTION,
            ),
            wait=True,
        )
        emojis = emojis.replace(" ", "")
        emoji_list = emojis.split(",")
        if len(emoji_list) > 10:
            await message.edit(
                embed=nextcord.Embed(
                    title="AutoEmoji - Error",
                    description="設定できる絵文字は10個までです。",
                    color=self.bot.color.ERROR,
                )
            )
            return
        for emoji in emoji_list:
            try:
                await message.add_reaction(emoji)
            except nextcord.Forbidden:
                description = "絵文字を追加する権限がありませんでした。"
            except nextcord.NotFound:
                description = "絵文字が見つかりませんでした。"
            except nextcord.InvalidArgument:
                description = "絵文字が無効です。"
            except nextcord.HTTPException:
                description = (
                    "絵文字がカンマ区切りで入力されているかご確認ください。\n"
                    "または...一時的なネットワークエラーが発生している可能性があります。"
                )
            else:
                continue
            await message.edit(
                embed=nextcord.Embed(
                    title="AutoEmoji - Error",
                    description=f"絵文字 {emoji} (`{emoji}`)の確認時にエラーが発生しました。\n{description}",
                    color=self.bot.color.ERROR,
                )
            )
            return
        try:
            await self.autoemoji_collection.update_one(
                filter={"channel_id": interaction.channel.id},
                update={"$set": {"emojis": emoji_list}},
                upsert=True,
            )
            self.autoemoji_cache[interaction.channel.id] = emoji_list
        except Exception as e:
            await message.edit(
                embed=nextcord.Embed(
                    title="AutoEmoji - Error",
                    description=f"エラーが発生しました。\n```{e}```",
                    color=self.bot.color.ERROR,
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
                color=self.bot.color.NORMAL,
            )
        )

    @application_checks.guild_only()
    @autoemoji_slash.subcommand(
        name="del",
        description="Delete autoemoji from this channel",
        description_localizations={
            nextcord.Locale.ja: "このチャンネルの自動絵文字を削除します。",
        },
    )
    async def del_autoemoji_slash(self, interaction: Interaction):
        assert interaction.guild is not None
        assert interaction.channel is not None

        await interaction.response.defer(ephemeral=False)

        delete_status = await self.autoemoji_collection.delete_one({"channel_id": interaction.channel.id})
        if delete_status.deleted_count == 0:
            await interaction.send(
                embed=nextcord.Embed(
                    title="AutoEmoji - Error",
                    description="このチャンネルには自動絵文字が設定されていません。",
                    color=self.bot.color.ERROR,
                ),
                ephemeral=True,
            )
            return
        await interaction.send(
            embed=nextcord.Embed(
                title="AutoEmoji - Success",
                description=(
                    "このチャンネルの自動絵文字を削除しました。\n"
                    "このメッセージにつく絵文字が最後の絵文字だよ..."
                ),
                color=self.bot.color.NORMAL,
            ),
            ephemeral=True,
        )
        self.autoemoji_cache.pop(interaction.channel.id, None)

    @application_checks.guild_only()
    @autoemoji_slash.subcommand(
        name="list",
        description="List autoemoji settings",
        description_localizations={
            nextcord.Locale.ja: "自動絵文字の設定を表示します。",
        },
    )
    async def list_autoemoji_slash(self, interaction: Interaction):
        assert interaction.channel is not None

        await interaction.response.defer(ephemeral=False)

        if interaction.channel.id not in self.autoemoji_cache:
            await interaction.send(
                embed=nextcord.Embed(
                    title="AutoEmoji - List",
                    description="このチャンネルには自動絵文字が設定されていません。",
                    color=self.bot.color.NORMAL,
                ),
                ephemeral=True,
            )
            return
        emoji_list = self.autoemoji_cache[interaction.channel.id]
        await interaction.send(
            embed=nextcord.Embed(
                title="AutoEmoji - List",
                description=(
                    "このチャンネルでリアクションするように設定されている絵文字は以下の通りです。\n"
                    f"{', '.join(emoji_list)}\n"
                    f"(`{', '.join(emoji_list)}`)"
                ),
                color=self.bot.color.NORMAL,
            ),
            ephemeral=True,
        )

    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message):
        if not message.guild:
            return
        if message.channel.id not in self.autoemoji_cache:
            return
        emoji_list = self.autoemoji_cache[message.channel.id]
        for emoji in emoji_list:
            try:
                await message.add_reaction(emoji)
            except Exception as e:
                logging.error(f"AutoEmoji - Error: {e}")
            await asyncio.sleep(1)


def setup(bot: NIRA):
    bot.add_cog(AutoEmoji(bot))
