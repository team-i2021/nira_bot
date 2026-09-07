import asyncio
import datetime
import importlib
import logging
import os
import random
import re
import sys
import typing

import nextcord
from bson import ObjectId
from motor import motor_asyncio
from nextcord import Interaction, SlashOption
from nextcord.ext import application_checks, commands, tasks

import util.srtr as srtr
from util import n_fc
from util.nira import NIRA

SYSDIR = sys.path[0]

_logger = logging.getLogger(__name__)

image_loc = f"{SYSDIR}/images"

ERSetting = typing.TypedDict(
    "ERSetting",
    {
        "_id": ObjectId,
        "guild_id": int,
        "trigger": str,
        "return": str | None,
        "mention": bool,
        "reaction": str | None,
    },
)


class NRSetting(typing.TypedDict):
    _id: int
    "設定が適応される場所のSnowflake ID"

    normal: bool
    "通常反応の有効/無効"

    extended: bool
    "拡張反応の有効/無効"


DBDelayMessage: typing.Final[str] = (
    "(データベースへの接続の最適化のため、実際に設定が適応されるまでに最大で30秒程かかる場合があります。)"
)


class ReactionControll(commands.Cog):
    def __init__(self, bot: NIRA):
        self.bot = bot
        self.er_collection: motor_asyncio.AsyncIOMotorCollection = self.bot.database[
            "er_setting"
        ]
        self.nr_collection: motor_asyncio.AsyncIOMotorCollection = self.bot.database[
            "nr_setting"
        ]

    @commands.has_permissions(manage_guild=True)
    @commands.group(
        name="er",
        help="""\
追加で新しいにらの反応を作り出すことが出来ます。
オートリプライとかって呼ばれるんですかね？まぁ、トリガーとリターンを指定することで、トリガーが送信された際に指定したリターンを送信することが出来ます。
トリガーには正規表現を使うことが出来ます。が、スペースを含むことはできませんのでご了承ください。

`n!er add [トリガー] [返信文] [メンション]`で追加できます。
`n!er del [トリガー]`で削除できます。
`n!er list`でリストを表示できます。
`n!er edit [トリガー] [新反応]`でトリガーを編集できます。

データベースへの接続の最適化のため、実際に設定が適応されるまでに最大で30秒程かかる場合があります。
""",
    )
    async def er_command(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.reply(
                embed=nextcord.Embed(
                    title="Error",
                    description=f"構文が異なります。\n```{self.bot.command_prefix}er [add/del/list/edit]```",
                    color=self.bot.color.ERROR,
                )
            )
        else:
            pass

    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    @er_command.command(name="add")
    async def er_add(
        self,
        ctx: commands.Context,
        trigger: str | None = None,
        return_text: str | None = None,
        mention: str = "False",
    ):
        assert ctx.guild

        if trigger is None or return_text is None:
            await ctx.reply(
                f"構文が異なります。\n```{self.bot.command_prefix}er add [トリガー] [返信文] [メンション(True/False)]```"
            )
        else:
            if mention in n_fc.on_ali:
                mention_setting = True
            elif mention in n_fc.off_ali:
                mention_setting = False
            else:
                await ctx.reply(
                    embed=nextcord.Embed(
                        title="Error",
                        description=f"返信に対するメンションの指定が不正です。\n`yes`や`True`又は、`off`や`False`で指定してください。",
                        color=0xFF0000,
                    )
                )
                return
            await self.er_collection.update_one(
                {"guild_id": ctx.guild.id, "trigger": trigger},
                {"$set": {"return": return_text, "mention": mention_setting}},
                upsert=True,
            )
            await ctx.reply(
                embed=nextcord.Embed(
                    title="Success",
                    description=f"トリガー`{trigger}`を追加しました。\nメンションは{'有効' if mention_setting else '無効'}です。\n{DBDelayMessage}",
                    color=0x00FF00,
                )
            )

    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    @er_command.command(name="del")
    async def er_del(self, ctx: commands.Context, trigger: str | None = None):
        assert ctx.guild
        if trigger is None:
            await ctx.reply(
                f"構文が異なります。\n```{self.bot.command_prefix}er del [トリガー]```"
            )
        else:
            if trigger == "all":
                await self.er_collection.delete_many({"guild_id": ctx.guild.id})
                await ctx.reply(
                    embed=nextcord.Embed(
                        title="Success",
                        description=f"全てのトリガーを削除しました。\n{DBDelayMessage}",
                        color=0x00FF00,
                    )
                )
            else:
                delete_status = await self.er_collection.delete_one(
                    {"guild_id": ctx.guild.id, "trigger": trigger}
                )
                if delete_status.deleted_count == 1:
                    await ctx.reply(
                        embed=nextcord.Embed(
                            title="Success",
                            description=f"トリガー`{trigger}`を削除しました。\n{DBDelayMessage}",
                            color=0x00FF00,
                        )
                    )
                else:
                    await ctx.reply(
                        embed=nextcord.Embed(
                            title="Error",
                            description=f"トリガー`{trigger}`は存在しませんでした。",
                            color=0xFF0000,
                        )
                    )

    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    @er_command.command(name="list")
    async def er_list(self, ctx: commands.Context):
        assert ctx.guild
        er_list: list[ERSetting] = await self.er_collection.find(
            {"guild_id": ctx.guild.id}
        ).to_list(length=None)
        if len(er_list) == 0:
            await ctx.reply(
                embed=nextcord.Embed(
                    title="Error",
                    description=f"追加反応が存在しません。",
                    color=0xFF0000,
                )
            )
        else:
            embed = nextcord.Embed(
                title="追加反応リスト",
                description=f"追加反応のリストです。",
                color=0x00FF00,
            )
            for er in er_list:
                embed.add_field(
                    name=er["trigger"],
                    value=f"- 返信文\n{er['return']}\n- メンション\n{'有効' if er['mention'] else '無効'}",
                    inline=False,
                )
            await ctx.author.send(embed=embed)

    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    @er_command.command(name="edit")
    async def er_edit(
        self,
        ctx: commands.Context,
        trigger: str | None = None,
        return_text: str | None = None,
        mention: str | None = None,
    ):
        assert ctx.guild
        if trigger is None or return_text is None:
            await ctx.reply(
                f"構文が異なります。\n```{self.bot.command_prefix}er edit [トリガー] [新反応] [*メンション]```"
            )
        else:
            if mention is None:
                set_value = {"return": return_text}
            else:
                if mention in n_fc.on_ali:
                    set_value = {"return": return_text, "mention": True}
                elif mention in n_fc.off_ali:
                    set_value = {"return": return_text, "mention": False}
                else:
                    await ctx.reply(
                        embed=nextcord.Embed(
                            title="Error",
                            description=f"返信に対するメンションの指定が不正です。\n`yes`や`True`又は、`off`や`False`で指定してください。",
                            color=0xFF0000,
                        )
                    )
                    return
            update_result = await self.er_collection.update_one(
                {"guild_id": ctx.guild.id, "trigger": trigger}, {"$set": set_value}
            )
            if update_result.modified_count == 0:
                await ctx.reply(
                    embed=nextcord.Embed(
                        title="Error",
                        description=f"トリガー`{trigger}`は存在しませんでした。",
                        color=0xFF0000,
                    )
                )
            else:
                await ctx.reply(
                    embed=nextcord.Embed(
                        title="Success",
                        description=f"トリガー`{trigger}`を編集しました。\n{DBDelayMessage}",
                        color=0x00FF00,
                    )
                )

    @nextcord.slash_command(name="er", description="Extended Reaction Setting")
    async def er_slash(self, interaction: Interaction):
        pass

    @application_checks.guild_only()
    @application_checks.has_permissions(manage_guild=True)
    @er_slash.subcommand(
        name="add",
        description="Add Extended Reaction Setting",
        description_localizations={nextcord.Locale.ja: "追加反応の設定追加"},
    )
    async def add_er_slash(
        self,
        interaction: Interaction,
        triggerMessage: str = SlashOption(
            name="trigger_message",
            name_localizations={nextcord.Locale.ja: "トリガーメッセージ"},
            description="Trigger message",
            description_localizations={nextcord.Locale.ja: "反応する部分です"},
            required=True,
        ),
        returnMessage: str | None = SlashOption(
            name="return_message",
            name_localizations={nextcord.Locale.ja: "返信メッセージ"},
            description="Return message",
            description_localizations={
                nextcord.Locale.ja: "返信するメッセージ内容です"
            },
            required=False,
            default=None,
        ),
        reactionEmoji: str | None = SlashOption(
            name="reaction_emoji",
            name_localizations={nextcord.Locale.ja: "リアクション絵文字"},
            description="Reaction emoji",
            description_localizations={
                nextcord.Locale.ja: "リアクションする絵文字です"
            },
            required=False,
            default=None,
        ),
        mention: bool = SlashOption(
            name="mention",
            name_localizations={nextcord.Locale.ja: "メンション"},
            description="Mention",
            description_localizations={
                nextcord.Locale.ja: "メンションするかどうかです"
            },
            required=False,
            choices={"Enable": True, "Disable": False},
            choice_localizations={
                nextcord.Locale.ja: {"Enable": "有効", "Disable": "無効"}
            },
            default=False,
        ),
    ):
        assert interaction.guild

        message = await interaction.send(
            embed=nextcord.Embed(
                title="Checking...",
                description="指定された絵文字を確認しています......",
                color=0x00FFFF,
            ),
            ephemeral=False,
        )

        if reactionEmoji is None and returnMessage is None:
            await message.edit(
                embed=nextcord.Embed(
                    title="Error",
                    description=f"返信文かリアクション絵文字のどちらかは指定してください。",
                    color=0xFF0000,
                )
            )
            return

        if reactionEmoji is not None:
            await message.edit(
                embed=nextcord.Embed(
                    title="Checking...",
                    description="指定された絵文字を確認しています......",
                    color=0x00FFFF,
                ),
            )
            try:
                if isinstance(message, nextcord.PartialInteractionMessage):
                    await (await message.fetch()).add_reaction(reactionEmoji)
                else:
                    await message.add_reaction(reactionEmoji)
            except Exception as e:
                await message.edit(
                    embed=nextcord.Embed(
                        title="Error",
                        description=f"リアクション絵文字の追加に失敗しました。\n{e}",
                        color=0xFF0000,
                    )
                )
                return

        await self.er_collection.update_one(
            {"guild_id": interaction.guild.id, "trigger": triggerMessage},
            {
                "$set": {
                    "return": returnMessage,
                    "mention": mention,
                    "reaction": reactionEmoji,
                }
            },
            upsert=True,
        )
        await message.edit(
            embed=nextcord.Embed(
                title="Success",
                description=f"追加反応を追加しました。\n{DBDelayMessage}",
                color=0x00FF00,
            )
        )

    @application_checks.guild_only()
    @application_checks.has_permissions(manage_guild=True)
    @er_slash.subcommand(
        name="list",
        description="List of Extended Reaction List",
        description_localizations={nextcord.Locale.ja: "追加反応の一覧"},
    )
    async def list_er_slash(self, interaction: Interaction):
        assert interaction.guild
        assert interaction.user

        await interaction.response.defer(ephemeral=True)
        er_list: list[ERSetting] = await self.er_collection.find(
            {"guild_id": interaction.guild.id}
        ).to_list(length=None)
        if len(er_list) == 0:
            await interaction.send(
                embed=nextcord.Embed(
                    title="Error",
                    description=f"追加反応が存在しません。",
                    color=0xFF0000,
                ),
                ephemeral=True,
            )
        else:
            embed = nextcord.Embed(
                title="追加反応リスト",
                description=f"追加反応のリストです。",
                color=0x00FF00,
            )
            for er in er_list:
                embed.add_field(
                    name=er["trigger"],
                    value=f"- 返信文\n{er.get("return", "(なし)")}\n\n- リアクション\n{er.get("reaction", "(なし)")}\n\n- メンション\n{'有効' if er['mention'] else '無効'}",
                    inline=False,
                )

            await interaction.user.send(embed=embed)
            await interaction.send("DMに送信しました。", ephemeral=True)

    @application_checks.guild_only()
    @application_checks.has_permissions(manage_guild=True)
    @er_slash.subcommand(
        name="del",
        description="Delete Extended Reaction Setting",
        description_localizations={nextcord.Locale.ja: "追加反応の削除"},
    )
    async def del_er_slash(
        self,
        interaction: Interaction,
        triggerMessage: str = SlashOption(
            name="trigger_message",
            name_localizations={nextcord.Locale.ja: "トリガーメッセージ"},
            description="Trigger message.",
            description_localizations={nextcord.Locale.ja: "トリガー。"},
            required=True,
        ),
    ):
        assert interaction.guild

        await interaction.response.defer(ephemeral=True)

        delete_result = await self.er_collection.delete_one(
            {"guild_id": interaction.guild.id, "trigger": triggerMessage}
        )
        if delete_result.deleted_count == 0:
            await interaction.followup.send(
                embed=nextcord.Embed(
                    title="Error",
                    description=f"追加反応が存在しませんでした。",
                    color=0xFF0000,
                )
            )
        else:
            await interaction.followup.send(
                embed=nextcord.Embed(
                    title="Success",
                    description=f"追加反応を削除しました。\n{DBDelayMessage}",
                    color=0x00FF00,
                )
            )

    @application_checks.guild_only()
    @application_checks.has_permissions(manage_guild=True)
    @er_slash.subcommand(
        name="edit",
        description="Edit Extended Reaction Setting",
        description_localizations={nextcord.Locale.ja: "追加反応の編集"},
    )
    async def edit_er_slash(
        self,
        interaction: Interaction,
        triggerMessage: str = SlashOption(
            name="trigger_message",
            name_localizations={nextcord.Locale.ja: "トリガーメッセージ"},
            description="Trigger message",
            description_localizations={nextcord.Locale.ja: "反応する部分です"},
            required=True,
        ),
        returnMessage: str = SlashOption(
            name="return_message",
            name_localizations={nextcord.Locale.ja: "返信メッセージ"},
            description="Return message",
            description_localizations={
                nextcord.Locale.ja: "返信するメッセージ内容です"
            },
            required=True,
        ),
        mention: bool = SlashOption(
            name="mention",
            name_localizations={nextcord.Locale.ja: "メンション"},
            description="Mention",
            description_localizations={
                nextcord.Locale.ja: "メンションをするかどうかです"
            },
            choices={"Enable": True, "Disable": False},
            choice_localizations={
                nextcord.Locale.ja: {"Enable": "有効", "Disable": "無効"}
            },
            required=False,
            default=False,
        ),
    ):
        assert interaction.guild

        await interaction.response.defer(ephemeral=True)
        update_value = {"return": returnMessage, "mention": mention}
        edit_result = await self.er_collection.update_one(
            {"guild_id": interaction.guild.id, "trigger": triggerMessage},
            {"$set": update_value},
        )
        if edit_result.modified_count == 0:
            await interaction.followup.send(
                embed=nextcord.Embed(
                    title="Error",
                    description=f"追加反応が存在しませんでした。",
                    color=0xFF0000,
                )
            )
        else:
            await interaction.followup.send(
                embed=nextcord.Embed(
                    title="Success",
                    description=f"追加反応を編集しました。\n{DBDelayMessage}",
                    color=0x00FF00,
                )
            )

    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    @commands.command(
        name="nr",
        help="""\
にらBOTのリアクション機能（Nira Reaction）を無効にしたりすることが出来ます。

`n!nr`: 今の状態を表示
`n!nr channel [normal|extended] off`: 指定した反応をチャンネルで無効化
`n!nr channel [normal|extended] on`: 指定した反応をチャンネルで有効化
`n!nr server [normal|extended] off`: 指定した反応を**サーバーで**無効化
`n!nr server [normal|extended] on`: 指定した反応を**サーバーで**有効化

- `normal`: にらBOTのデフォルトの反応（「にら」などに反応して起こるリアクション）
- `extended`: 追加反応（`er`コマンドを使いサーバー毎に設定することが出来るリアクション）

データベースへの接続の最適化のため、実際に設定が適応されるまでに最大で30秒程かかる場合があります。

※サーバーで反応が無効化された場合、チャンネルで有効化しても反応しません。""",
    )
    async def nr(
        self,
        ctx: commands.Context,
        target: typing.Literal["channel", "server"] | None = None,
        reaction_type: typing.Literal["normal", "extended"] | None = None,
        setting: str | None = None,
    ):
        assert ctx.guild

        prefix = ctx.prefix

        if target is None:
            guild_reaction: NRSetting | None = await self.nr_collection.find_one(
                {"_id": ctx.guild.id}
            )
            channel_reaction: NRSetting | None = await self.nr_collection.find_one(
                {"_id": ctx.channel.id}
            )

            embed = nextcord.Embed(
                title="リアクション設定",
                description="以下がリアクションの設定です。",
                color=0x00FF00,
            )

            if guild_reaction:
                embed.add_field(
                    name="サーバー",
                    value=f"通常反応: `{'有効' if guild_reaction['normal'] else '無効'}`\n拡張反応: `{'有効' if guild_reaction['extended'] else '無効'}`",
                    inline=False,
                )
            else:
                embed.add_field(
                    name="サーバー",
                    value="通常反応: `有効`\n拡張反応: `有効`",
                    inline=False,
                )

            if channel_reaction:
                embed.add_field(
                    name="チャンネル",
                    value=f"通常反応: `{'有効' if channel_reaction['normal'] else '無効'}`\n拡張反応: `{'有効' if channel_reaction['extended'] else '無効'}`",
                    inline=False,
                )
            else:
                embed.add_field(
                    name="チャンネル",
                    value="通常反応: `有効`\n拡張反応: `有効`",
                    inline=False,
                )

            await ctx.send(embed=embed)

        elif target in ["channel", "server"]:
            if reaction_type is None or reaction_type not in ["normal", "extended"]:
                await ctx.reply(
                    f"引数が不正です。\n```{prefix}nr [channel/server] [normal/extended] [on/off]```"
                )
                return
            if setting is None or (
                setting not in n_fc.on_ali and setting not in n_fc.off_ali
            ):
                await ctx.reply(
                    f"引数が不正です。\n```{prefix}nr [channel/server] [normal/extended] [on/off]```"
                )
                return

            current_setting: NRSetting | None = await self.nr_collection.find_one(
                {"_id": ctx.guild.id if target == "server" else ctx.channel.id}
            )

            if current_setting is None:
                if setting in n_fc.off_ali:
                    if reaction_type == "normal":
                        new_setting = {
                            "_id": (
                                ctx.guild.id if target == "server" else ctx.channel.id
                            ),
                            "normal": setting in n_fc.on_ali,
                            "extended": True,
                        }
                    else:
                        new_setting = {
                            "_id": (
                                ctx.guild.id if target == "server" else ctx.channel.id
                            ),
                            "normal": True,
                            "extended": setting in n_fc.on_ali,
                        }
                    await self.nr_collection.insert_one(new_setting)
            else:
                if (
                    setting in n_fc.on_ali
                    and current_setting[
                        "normal" if reaction_type == "extended" else "extended"
                    ]
                ):
                    await self.nr_collection.delete_one(
                        {
                            "_id": (
                                ctx.guild.id if target == "server" else ctx.channel.id
                            ),
                        }
                    )
                else:
                    await self.nr_collection.update_one(
                        {
                            "_id": (
                                ctx.guild.id if target == "server" else ctx.channel.id
                            ),
                        },
                        {"$set": {reaction_type: setting in n_fc.on_ali}},
                        upsert=True,
                    )

            await ctx.reply(
                (
                    "リアクションの設定を更新しました。\n"
                    "※サーバーで反応が無効化された場合、チャンネルで有効化しても反応しません。\n"
                    if target == "server" and setting in n_fc.off_ali
                    else "" f"{DBDelayMessage}"
                )
            )

        else:
            await ctx.reply(
                f"引数が不正です。\n```{prefix}nr [channel/server] [on/off]```"
            )

    @nextcord.slash_command(name="nr", description="Nira Reaction Setting")
    async def nr_slash(self, interaction: Interaction):
        pass

    @nr_slash.subcommand(
        name="channel", description="Setting of Nira Reaction in Channel"
    )
    async def channel_nr_slash(self, interaction: Interaction):
        pass

    @application_checks.guild_only()
    @application_checks.has_permissions(manage_guild=True)
    @channel_nr_slash.subcommand(
        name="normal", description="Setting of Normal Reaction in Channel"
    )
    async def channel_normal_nr_slash(
        self,
        interaction: Interaction,
        setting: bool = SlashOption(
            name="setting",
            name_localizations={nextcord.Locale.ja: "設定"},
            description="Enable or Disable",
            description_localizations={
                nextcord.Locale.ja: "有効にするか、無効にするか"
            },
            required=True,
        ),
    ):
        assert interaction.channel

        await interaction.response.defer(ephemeral=True)
        current_setting: NRSetting | None = await self.nr_collection.find_one(
            {"_id": interaction.channel.id}
        )
        if current_setting is None:
            if not setting:
                new_setting = {
                    "_id": interaction.channel.id,
                    "normal": setting,
                    "extended": True,
                }
                await self.nr_collection.insert_one(new_setting)
        else:
            if setting and current_setting["extended"]:
                await self.nr_collection.delete_one({"_id": interaction.channel.id})
            else:
                await self.nr_collection.update_one(
                    {"_id": interaction.channel.id},
                    {"$set": {"normal": setting}},
                    upsert=True,
                )

        await interaction.send(
            f"リアクションの設定を更新しました。\n{DBDelayMessage}", ephemeral=True
        )

    @application_checks.guild_only()
    @application_checks.has_permissions(manage_guild=True)
    @channel_nr_slash.subcommand(
        name="extended", description="Setting of Extended Reaction in Channel"
    )
    async def channel_extended_nr_slash(
        self,
        interaction: Interaction,
        setting: bool = SlashOption(
            name="setting",
            name_localizations={nextcord.Locale.ja: "設定"},
            description="Enable or Disable",
            description_localizations={
                nextcord.Locale.ja: "有効にするか、無効にするか"
            },
            required=True,
        ),
    ):
        assert interaction.channel

        await interaction.response.defer(ephemeral=True)
        current_setting: NRSetting | None = await self.nr_collection.find_one(
            {"_id": interaction.channel.id}
        )
        if current_setting is None:
            if not setting:
                new_setting = {
                    "_id": interaction.channel.id,
                    "normal": True,
                    "extended": setting,
                }
                await self.nr_collection.insert_one(new_setting)
        else:
            if setting and current_setting["normal"]:
                await self.nr_collection.delete_one({"_id": interaction.channel.id})
            else:
                await self.nr_collection.update_one(
                    {"_id": interaction.channel.id},
                    {"$set": {"extended": setting}},
                    upsert=True,
                )

        await interaction.send(
            f"リアクションの設定を更新しました。\n{DBDelayMessage}", ephemeral=True
        )

    @nr_slash.subcommand(
        name="server", description="Setting of Nira Reaction in Server"
    )
    async def server_nr_slash(self, interaction: Interaction):
        pass

    @application_checks.guild_only()
    @application_checks.has_permissions(manage_guild=True)
    @server_nr_slash.subcommand(
        name="normal", description="Setting of Normal Reaction in Server"
    )
    async def server_normal_nr_slash(
        self,
        interaction: Interaction,
        setting: bool = SlashOption(
            name="setting",
            name_localizations={nextcord.Locale.ja: "設定"},
            description="Enable or Disable",
            description_localizations={
                nextcord.Locale.ja: "有効にするか、無効にするか"
            },
            required=True,
        ),
    ):
        assert interaction.guild

        await interaction.response.defer(ephemeral=True)
        current_setting: NRSetting | None = await self.nr_collection.find_one(
            {"_id": interaction.guild.id}
        )
        if current_setting is None:
            if not setting:
                new_setting = {
                    "_id": interaction.guild.id,
                    "normal": setting,
                    "extended": True,
                }
                await self.nr_collection.insert_one(new_setting)
        else:
            if setting and current_setting["extended"]:
                await self.nr_collection.delete_one({"_id": interaction.guild.id})
            else:
                await self.nr_collection.update_one(
                    {"_id": interaction.guild.id},
                    {"$set": {"normal": setting}},
                    upsert=True,
                )

        await interaction.send(
            f"リアクションの設定を更新しました。\n{DBDelayMessage}", ephemeral=True
        )

    @application_checks.guild_only()
    @application_checks.has_permissions(manage_guild=True)
    @server_nr_slash.subcommand(
        name="extended", description="Setting of Extended Reaction in Server"
    )
    async def server_extended_nr_slash(
        self,
        interaction: Interaction,
        setting: bool = SlashOption(
            name="setting",
            name_localizations={nextcord.Locale.ja: "設定"},
            description="Enable or Disable",
            description_localizations={
                nextcord.Locale.ja: "有効にするか、無効にするか"
            },
            required=True,
        ),
    ):
        assert interaction.guild

        await interaction.response.defer(ephemeral=True)
        current_setting: NRSetting | None = await self.nr_collection.find_one(
            {"_id": interaction.guild.id}
        )
        if current_setting is None:
            if not setting:
                new_setting = {
                    "_id": interaction.guild.id,
                    "normal": True,
                    "extended": setting,
                }
                await self.nr_collection.insert_one(new_setting)
        else:
            if setting and current_setting["normal"]:
                await self.nr_collection.delete_one({"_id": interaction.guild.id})
            else:
                await self.nr_collection.update_one(
                    {"_id": interaction.guild.id},
                    {"$set": {"extended": setting}},
                    upsert=True,
                )

        await interaction.send(
            f"リアクションの設定を更新しました。\n{DBDelayMessage}", ephemeral=True
        )

    @application_checks.guild_only()
    @application_checks.has_permissions(manage_guild=True)
    @nr_slash.subcommand(
        name="status", description="Display the status of Nira Reaction"
    )
    async def status_nr_slash(self, interaction: Interaction):
        assert interaction.guild
        assert interaction.channel

        guild_reaction: NRSetting | None = await self.nr_collection.find_one(
            {"_id": interaction.guild.id}
        )
        channel_reaction: NRSetting | None = await self.nr_collection.find_one(
            {"_id": interaction.channel.id}
        )

        embed = nextcord.Embed(
            title="リアクション設定",
            description="以下がリアクションの設定です。",
            color=0x00FF00,
        )

        if guild_reaction:
            embed.add_field(
                name="サーバー",
                value=f"通常反応: `{'有効' if guild_reaction['normal'] else '無効'}`\n拡張反応: `{'有効' if guild_reaction['extended'] else '無効'}`",
                inline=False,
            )
        else:
            embed.add_field(
                name="サーバー",
                value="通常反応: `有効`\n拡張反応: `有効`",
                inline=False,
            )

        if channel_reaction:
            embed.add_field(
                name="チャンネル",
                value=f"通常反応: `{'有効' if channel_reaction['normal'] else '無効'}`\n拡張反応: `{'有効' if channel_reaction['extended'] else '無効'}`",
                inline=False,
            )
        else:
            embed.add_field(
                name="チャンネル",
                value="通常反応: `有効`\n拡張反応: `有効`",
                inline=False,
            )

        await interaction.send(embed=embed, ephemeral=True)

    @application_checks.is_owner()
    @nr_slash.subcommand(
        name="updated",
        description="Displays the last time the reaction database was retrieved.",
    )
    async def updated_nr_slash(self, interaction: Interaction):
        cog = self.bot.get_cog("NormalReaction")
        if cog:
            try:
                last_update: str | None = getattr(cog, "last_update")
                await interaction.send(
                    (
                        last_update
                        if last_update
                        else "まだデータが読み込まれていません。"
                    ),
                    ephemeral=True,
                )
            except AttributeError:
                await interaction.send(
                    "現在このBOTでは反応する機能は正常に動作していません。",
                    ephemeral=True,
                )
        else:
            await interaction.send(
                "現在このBOTでは反応する機能は有効化されていません。", ephemeral=True
            )


class Reaction:
    "リアクションの基底クラス。"

    _trigger: str
    trigger: re.Pattern

    def __init__(self, trigger: str):
        self._trigger = trigger
        self.trigger = re.compile(trigger)

    def check(self, message: nextcord.Message) -> bool:
        "指定された文字列がトリガーにマッチするかどうかを返す。"
        return bool(self.trigger.search(message.content))

    def get(self):
        "リアクションを返す。"
        raise NotImplementedError

    async def reaction(self, message: nextcord.Message) -> nextcord.Message | None:
        "リアクションを行い、返信メッセージを返す。"
        raise NotImplementedError


class FileReaction(Reaction):
    "ファイルを添付するリアクション。"

    file: list[str]

    def __init__(self, trigger: str, *file: str):
        super().__init__(trigger)
        self.file = list(file)

    def get(self) -> nextcord.File:
        return nextcord.File(os.path.join(image_loc, random.choice(self.file)))

    async def reaction(self, message: nextcord.Message) -> nextcord.Message | None:
        return await message.reply(file=self.get())


class DesignatedFileReaction(FileReaction):
    "指定されたGuildでのみファイルを添付するリアクション。"

    async def reaction(self, message: nextcord.Message) -> nextcord.Message | None:
        if (
            isinstance(message.guild, nextcord.Guild)
            and message.guild.id in n_fc.GUILD_IDS
        ):
            return await message.reply(file=self.get())
        return None


class TextReaction(Reaction):
    "テキストを返信するリアクション。"

    text: list[str]

    def __init__(self, trigger: str, *text: str):
        super().__init__(trigger)
        self.text = list(text)

    def get(self) -> str:
        return random.choice(self.text)

    async def reaction(self, message: nextcord.Message) -> nextcord.Message | None:
        return await message.reply(self.get())


class DesignatedTextReaction(TextReaction):
    "指定されたGuildでのみテキストを返信するリアクション。"

    async def reaction(self, message: nextcord.Message) -> nextcord.Message | None:
        if (
            isinstance(message.guild, nextcord.Guild)
            and message.guild.id in n_fc.GUILD_IDS
        ):
            return await message.reply(self.get())
        return None


class EmojiReaction(Reaction):
    "絵文字を付けるリアクション。"

    emoji: str

    def __init__(self, trigger: str, emoji: str):
        super().__init__(trigger)
        self.emoji = emoji

    def get(self) -> str:
        return self.emoji

    async def reaction(self, message: nextcord.Message) -> None:
        await message.add_reaction(self.get())


NiraRegex: typing.Final[str] = (
    r"にら|ニラ|nira|garlic|韮|Chinese chives|Allium tuberosum"
)
AndNira: typing.Final[str] = r"^(?=.*({}))".format(NiraRegex) + r"(?=.*({})).*$"

Reactions: typing.Final[list[Reaction]] = [
    TextReaction(r"(´・ω・｀)", "(´・ω・｀)"),
    TextReaction(r"^(?=.*草)(?!.*元素).*$", "草", "くそわろたｧ!!!"),
    TextReaction("https://www.nicovideo.jp", "ニコニコだぁ！"),
    TextReaction("https://www.youtube.com", "ようつべぇ...？"),
    TextReaction("https://(twitter|x).com", "ついったぁ！！！"),
    DesignatedFileReaction(
        r"[こコｺ][いイｲ][きキｷ][んンﾝ][ぐグｸﾞ]|[いイｲ][とトﾄ][こコｺ][いイｲ]|itokoi",
        "itokoi_1.jpg",
        "itokoi_2.jpg",
        "itokoi_3.jpg",
        "itokoi_4.jpg",
        "itokoi_5.jpg",
        "itokoi_6.jpg",
    ),
    FileReaction(
        AndNira.format("栽培|さいばい|サイバイ"),
        "nira_saibai_1.jpg",
        "nira_saibai_2.jpg",
    ),
    DesignatedFileReaction(AndNira.format("伊藤|いとう|イトウ"), "nira_itou.jpg"),
    FileReaction(
        AndNira.format("ごはん|飯|らいす|ライス|[Rr][Ii][Cc][Ee]"), "nira_rice.jpg"
    ),
    FileReaction(AndNira.format("枯|かれ|カレ"), "nira_kare.jpg"),
    FileReaction(
        AndNira.format("魚|さかな|fish|サカナ|ざかな|ザカナ"), "nira_fish.jpg"
    ),
    FileReaction(AndNira.format("独裁|どくさい|ドクサイ"), "nira_dokusai.jpg"),
    FileReaction(AndNira.format("成長|せいちょう|セイチョウ"), "nira_grow.jpg"),
    FileReaction(AndNira.format("なべ|鍋|ナベ"), "nira_nabe.jpg"),
    FileReaction(AndNira.format("かりばー|カリバー|剣"), "nira_sword.jpg"),
    FileReaction(AndNira.format("あんど|and|アンド"), "nira_and.jpg"),
    FileReaction(AndNira.format("らんど|ランド|rand|land"), "nira_land.jpg"),
    FileReaction(AndNira.format("饅頭|まんじゅう|マンジュウ"), "nira_manju.jpg"),
    FileReaction(AndNira.format("レバ|れば"), "rebanira.jpg"),
    FileReaction(
        AndNira.format("とり|トリ|bird|鳥"), "nira_tori_1.jpg", "nira_tori_2.jpg"
    ),
    TextReaction(
        AndNira.format("twitter|Twitter|TWITTER|ついったー|ツイッター"),
        "https://x.com/niranuranura",
    ),
    FileReaction(NiraRegex, "nira_1.jpg", "nira_2.jpg", "nira_3.png", "nira_4.jpg"),
    FileReaction("ぴの|ピノ|pino", "pino_1.jpg", "pino_2.jpg", "pino_3.jpg"),
    FileReaction("きつね|キツネ|狐", "fox_1.jpg", "fox_2.jpg"),
    FileReaction("ういろ", "uiro_1.jpg", "uiro_2.jpg"),
    FileReaction(
        "りんご|リンゴ|[Aa][Pp]{2}[1Ll][Ee]|アップル|あっぷる|林檎|maçã", "apple.jpg"
    ),
    DesignatedFileReaction(
        "しゃけ|シャケ|さけ|サケ|鮭|syake|salmon|さーもん|サーモン",
        "salmon_1.jpg",
        "salmon_2.jpg",
        "salmon_3.jpg",
    ),
    EmojiReaction(
        "な(つ|っちゃん)|[Nn][Aa][Tt][Tt][Yy][Aa][Nn]", "<:natsu:908565532268179477>"
    ),
    DesignatedFileReaction("みけ|ミケ|三毛", "mike.mp4"),
    FileReaction("せろり|セロリ", "serori.jpg"),
    DesignatedFileReaction("ろり|ロリ", "rori_1.jpg", "rori_2.jpg"),
    DesignatedTextReaction(
        r"^(?=.*ｸｧ|くあっ|クアッ|クァ|くぁ|くわぁ|クワァ)(?!.*バックアップ|ばっくあっぷ).*$",
        "ﾜｰｽｹﾞｪｽｯｹﾞｸｧｯｸｧｯｸｧwwwww",
    ),
    TextReaction(
        "ふぇにっくす|フェニックス|不死鳥|ふしちょう|phoenix|焼き鳥|やきとり",
        "https://www.google.com/search?q=%E3%81%93%E3%81%AE%E8%BF%91%E3%81%8F%E3%81%AE%E7%84%BC%E3%81%8D%E9%B3%A5%E5%B1%8B",
    ),
    DesignatedFileReaction(
        "(かな|悲)しい|(つら|辛)い|ぴえん|かわいそう|泣(きそう|く)|:pleading_face:|:cry:|:sob:|:weary:|:smiling_face_with_tear:",
        "kawaisou.png",
    ),
    FileReaction("さばかん|鯖缶|サバカン", "sabakan.jpg"),
    DesignatedFileReaction("訴え|訴訟", "sosyou.jpg"),
    FileReaction("しゅうじん|囚人|シュウジン|罪人", "syuuzin.png"),
    FileReaction(
        "bsod|BSOD|ブルスク|ブルースクリーン|ブラックスクリーン",
        "bsod_1.jpg",
        "bsod_2.jpg",
    ),
    TextReaction(
        "黒棺|くろひつぎ|藍染隊長|クロヒツギ|あいぜんそうすけ",
        (
            "滲み出す混濁の紋章、不遜なる狂気の器\n"
            "湧き上がり・否定し・痺れ・瞬き・眠りを妨げる\n"
            "爬行する鉄の王女　絶えず自壊する泥の人形\n"
            "結合せよ　反発せよ　地に満ち己の無力を知れ...\n"
            "破道の九十・黒棺！\n"
        ),
        "まったく............やりにくい男だ............\n破道の九十......黒棺",
    ),
    TextReaction(
        "昼ごはん|ひるごはん|昼ご飯|ひるご飯",
        "https://cookpad.com/search/%E4%BB%8A%E6%97%A5%E3%81%AE%E3%83%A9%E3%83%B3%E3%83%81",
    ),
]


class NormalReaction(commands.Cog):
    def __init__(self, bot: NIRA):
        self.bot = bot
        self.ex_reaction_list: list[ERSetting] = []
        self.nr_setting_list: list[NRSetting] = []
        self.SLEEP_TIMER = 3
        self.REACTION_ID = "<:trash:908565976407236608>"
        self.last_update: str | None = None

        self.er_collection: motor_asyncio.AsyncIOMotorCollection = self.bot.database[
            "er_setting"
        ]
        "ユーザーが設定できる、カスタマイズ可能なオートリプライの設定コレクション"

        self.nr_collection: motor_asyncio.AsyncIOMotorCollection = self.bot.database[
            "nr_setting"
        ]
        "にらBOTのリアクションを制御する設定コレクション"

        self.database_update_loop.start()

    def cog_unload(self):
        self.database_update_loop.cancel()

    async def database_update(self) -> None:
        """
        コレクションからデータを取得し、リストを更新する関数。
        """
        self.ex_reaction_list = await self.er_collection.find().to_list(length=None)
        self.nr_setting_list = await self.nr_collection.find().to_list(length=None)
        self.last_update = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")

    async def after_reaction(self, message: nextcord.Message) -> None:
        """
        リアクションメッセージを送信した後に、絵文字リアクションを付与し、メッセージを削除できるようにする関数。
        """
        assert self.bot.user
        await message.add_reaction(self.REACTION_ID)
        await asyncio.sleep(self.SLEEP_TIMER)
        try:
            await message.remove_reaction(self.REACTION_ID, self.bot.user)
        except Exception:
            pass

    @commands.Cog.listener()
    async def on_reaction_add(
        self, reaction: nextcord.Reaction, member: nextcord.Member
    ):
        assert self.bot.user

        if reaction.message.author != self.bot.user:
            return

        if member == self.bot.user:
            return

        if str(reaction.emoji) == self.REACTION_ID:
            try:
                await reaction.message.delete()
            except Exception:
                pass

    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message):
        assert self.bot.user

        if message.author.bot:
            # アプリケーションが送信したメッセージには反応しない。
            return

        if isinstance(
            message.channel,
            (
                nextcord.DMChannel,
                nextcord.Thread,
                nextcord.GroupChannel,
                nextcord.PartialMessageable,
            ),
        ):
            # DM、スレッド、グループチャンネルには反応しない。
            return

        assert message.guild

        if self.bot.debug and message.guild.id not in n_fc.GUILD_IDS:
            # BOTがデバッグモードの際は、指定されたサーバー以外には反応しない。
            return

        if (
            isinstance(self.bot.command_prefix, str)
            and message.content.startswith(self.bot.command_prefix)
            or isinstance(self.bot.command_prefix, (list, tuple))
            and any(
                message.content.startswith(prefix) for prefix in self.bot.command_prefix
            )
        ):
            # コマンドプレフィックスで始まるメッセージには反応しない。
            return

        if message.content.endswith("."):
            # ピリオドで終わるメッセージには反応しない。
            return

        if (
            not isinstance(message.channel, nextcord.VoiceChannel)
            and message.channel.topic
            and "nira-off" in message.channel.topic
        ):
            # チャンネルトピックに「nira-off」と記述されている場合は反応しない。
            return

        normal_reaction: bool = True
        "通常のリアクションを行うかどうかのブール値"

        extedned_reaction: bool = True
        "拡張リアクションを行うかどうかのブール値"

        guild_reactions = [
            d for d in self.nr_setting_list if d["_id"] == message.guild.id
        ]

        guild_reaction: NRSetting | None = None

        if len(guild_reactions) > 0:
            guild_reaction = guild_reactions[0]

            if not guild_reaction["normal"]:
                normal_reaction = False

            if not guild_reaction["extended"]:
                extedned_reaction = False

            if len(guild_reactions) > 1:
                self.nr_setting_list = [
                    d for d in self.nr_setting_list if d["_id"] != message.guild.id
                ]
                await self.nr_collection.delete_many({"_id": message.guild.id})
                self.nr_setting_list.append(guild_reaction)
                await self.nr_collection.insert_one(guild_reaction)

        channel_reactions = [
            d for d in self.nr_setting_list if d["_id"] == message.channel.id
        ]

        channel_reaction: NRSetting | None = None

        if len(channel_reactions) > 0:
            channel_reaction = channel_reactions[0]

            if not channel_reaction["normal"]:
                normal_reaction = False

            if not channel_reaction["extended"]:
                extedned_reaction = False

            if len(channel_reactions) > 1:
                self.nr_setting_list = [
                    d for d in self.nr_setting_list if d["_id"] != message.channel.id
                ]
                await self.nr_collection.delete_many({"_id": message.channel.id})
                self.nr_setting_list.append(channel_reaction)
                await self.nr_collection.insert_one(channel_reaction)

        # 追加反応
        if extedned_reaction:
            ex_reaction_list = [
                d
                for d in self.ex_reaction_list
                if d["guild_id"] == message.guild.id
                and re.search(d["trigger"], message.content)
            ]
            for reaction in ex_reaction_list:
                reaction_content = reaction.get("return", None)
                reaction_emoji = reaction.get("reaction", None)

                if reaction_emoji is not None:
                    try:
                        await message.add_reaction(reaction_emoji)
                    except Exception:
                        pass

                if reaction_content is not None:
                    reaction_contents: list[str] = []
                    join_check = False
                    for c in reaction_content.split("|"):
                        if c == "":
                            join_check = True
                            continue
                        if join_check:
                            if len(reaction_contents) == 0:
                                reaction_contents.append(c)
                                join_check = False
                            else:
                                reaction_contents[-1] += f"|{c}"
                                join_check = False
                        else:
                            reaction_contents.append(c)
                    if len(reaction_contents) == 1:
                        await message.reply(
                            reaction_content, mention_author=reaction["mention"]
                        )
                    elif len(reaction_contents) > 1:
                        await message.reply(
                            random.choice(reaction_contents),
                            mention_author=reaction["mention"],
                        )

        # 通常反応
        if normal_reaction:
            try:
                for reaction in Reactions:
                    if reaction.check(message):
                        result = await reaction.reaction(message)
                        if result:
                            await self.after_reaction(result)
                        return
            except Exception:
                pass

        if channel_reaction:
            if channel_reaction["normal"] and channel_reaction["extended"]:
                self.nr_setting_list = [
                    d for d in self.nr_setting_list if d["_id"] != message.channel.id
                ]
                await self.nr_collection.delete_one({"_id": message.channel.id})

        if guild_reaction:
            if guild_reaction["normal"] and guild_reaction["extended"]:
                self.nr_setting_list = [
                    d for d in self.nr_setting_list if d["_id"] != message.guild.id
                ]
                await self.nr_collection.delete_one({"_id": message.guild.id})

    @tasks.loop(seconds=30)
    async def database_update_loop(self):
        try:
            await self.database_update()
        except Exception:
            _logger.exception("An error has occurred")


def setup(bot: NIRA):
    importlib.reload(srtr)
    bot.add_cog(ReactionControll(bot))
    bot.add_cog(NormalReaction(bot))
