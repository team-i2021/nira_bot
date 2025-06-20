import enum
from typing import NamedTuple

import nextcord
from motor import motor_asyncio
from nextcord import ForumTag, Interaction
from nextcord.ext import application_checks, commands

from util.nira import NIRA


class AutoTagMode(enum.Enum):
    STATUS = 0
    ON = 1
    OFF = 2


class AutoTagResult(NamedTuple):
    message: str | None
    embed: nextcord.Embed | None


# Autorole
class AutoTag(commands.Cog):
    def __init__(self, bot: NIRA):
        self.bot = bot
        self.collection: motor_asyncio.AsyncIOMotorCollection = self.bot.database[
            "autotag"
        ]

    async def autotag_message(
        self,
        mode: AutoTagMode,
        interaction: Interaction | commands.Context,
        forum_id: int | None = None,
        tags: list[ForumTag] = [],
    ) -> AutoTagResult:
        assert isinstance(interaction.guild, nextcord.Guild)

        if mode == AutoTagMode.ON:
            if len(tags) == 0:
                return AutoTagResult(
                    "自動タグ付け\nエラー: タグが指定されていません。\nこのフォーラムに、自動で付けたいタグをつけてから同じコマンドを入力してください。",
                    None,
                )
            await self.collection.update_one(
                {"channel_id": forum_id},
                {"$set": {"tags": [t.id for t in tags]}},
                upsert=True,
            )
            return AutoTagResult(
                None,
                nextcord.Embed(
                    title="自動タグ付け",
                    description=f"設定完了: {', '.join([t.name for t in tags])} のタグを自動的に追加します。",
                    color=self.bot.color.NORMAL,
                ),
            )

        elif mode == AutoTagMode.OFF:
            result = await self.collection.delete_one({"channel_id": forum_id})
            if result.deleted_count == 0:
                return AutoTagResult(
                    "このフォーラムチャンネルで自動タグ付けは設定されていません。",
                    None,
                )
            else:
                return AutoTagResult(
                    "このフォーラムチャンネルで自動タグ付けを無効にしました。",
                    None,
                )

        else:
            result = await self.collection.find_one({"channel_id": forum_id})
            if result is not None:
                msg = f"このフォーラムチャンネル自動タグ付けは有効です。\n自動で付けられるタグは {', '.join([t.name for t in tags])} です。"
            else:
                msg = "このフォーラムチャンネルで自動タグ付けは設定されていません。"

            if isinstance(interaction, Interaction):
                usage = "`/autotag on` / `/autotag off` / `/autotag status`"
            else:
                usage = f"`{interaction.prefix}autotag on` / `{interaction.prefix}autotag off`"

            return AutoTagResult(
                None,
                nextcord.Embed(
                    title="自動タグ付け", description=f"{msg}\n{usage}", color=0x00FF00
                ),
            )

    @nextcord.slash_command(name="autotag", description="自動タグ付け")
    async def autotag(self, interaction: Interaction):
        pass

    @application_checks.guild_only()
    @application_checks.has_permissions(manage_roles=True)
    @autotag.subcommand(name="off", description="自動タグ付けを無効にします")
    async def autotag_off(self, interaction: Interaction):
        if not isinstance(interaction.channel, nextcord.Thread):
            await interaction.send(
                "このコマンドはフォーラムの投稿内でのみ使用できます。",
                ephemeral=True,
            )
            return

        if not isinstance(interaction.channel.parent, nextcord.ForumChannel):
            await interaction.send(
                "このコマンドはフォーラムチャンネルでのみ使用できます。",
                ephemeral=True,
            )
            return

        result = await self.autotag_message(
            AutoTagMode.OFF, interaction, interaction.channel.parent.id
        )

        if result.embed:
            await interaction.send(result.message, embed=result.embed, ephemeral=True)
        else:
            await interaction.send(result.message, ephemeral=True)

    @application_checks.guild_only()
    @application_checks.has_permissions(manage_roles=True)
    @autotag.subcommand(
        name="on", description="フォーラムに投稿があったときに自動的にタグ付けします"
    )
    async def autotag_on(self, interaction: Interaction):
        if not isinstance(interaction.channel, nextcord.Thread):
            await interaction.send(
                "このコマンドはフォーラムの投稿内でのみ使用できます。",
                ephemeral=True,
            )
            return

        if not isinstance(interaction.channel.parent, nextcord.ForumChannel):
            await interaction.send(
                "このコマンドはフォーラムチャンネルでのみ使用できます。",
                ephemeral=True,
            )
            return

        tags = interaction.channel.applied_tags

        if not tags:
            await interaction.send(
                "この投稿にはタグが設定されていません。\nまずはこのフォーラムに投稿があった際に自動で付けたいタグを、この投稿に設定してください。",
                ephemeral=True,
            )
            return

        result = await self.autotag_message(
            AutoTagMode.ON,
            interaction,
            interaction.channel.parent.id,
            tags,
        )

        if result.embed:
            await interaction.send(result.message, embed=result.embed, ephemeral=True)
        else:
            await interaction.send(result.message, ephemeral=True)

    @application_checks.guild_only()
    @autotag.subcommand(name="status", description="自動ロールの設定状態を確認します")
    async def autotag_status(self, interaction: Interaction):
        if not isinstance(interaction.channel, nextcord.Thread):
            await interaction.send(
                "このコマンドはフォーラムの投稿内でのみ使用できます。",
                ephemeral=True,
            )
            return

        if not isinstance(interaction.channel.parent, nextcord.ForumChannel):
            await interaction.send(
                "このコマンドはフォーラムチャンネルでのみ使用できます。",
                ephemeral=True,
            )
            return

        result = await self.autotag_message(
            AutoTagMode.STATUS, interaction, interaction.channel.parent.id
        )
        if result.embed:
            await interaction.send(result.message, embed=result.embed, ephemeral=True)
        else:
            await interaction.send(result.message, ephemeral=True)

    @commands.Cog.listener()
    async def on_thread_create(self, thread: nextcord.Thread):
        channel = thread.parent
        if channel is None or not isinstance(channel, nextcord.ForumChannel):
            return
        result = await self.collection.find_one({"channel_id": channel.id})
        if result:
            tags = [channel.get_tag(tid) for tid in result.get("tags", []) if tid]
            if tags:
                await thread.edit(applied_tags=[t for t in tags if t])


def setup(bot: NIRA):
    bot.add_cog(AutoTag(bot))
