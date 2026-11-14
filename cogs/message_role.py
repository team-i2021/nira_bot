import logging
import re
import sys
from collections.abc import Sequence
from typing import Self

import nextcord
from motor import motor_asyncio
from nextcord import Interaction
from nextcord.ext import application_checks, commands

from util import admin_check, modal
from util.nira import NIRA

ROLE_ID = re.compile(r"<@&[\d]+?>")

# 特定のチャンネルにて特定のメッセージが送信された場合にロールをつけるそれ。
# データ形式:MongoDB

SYSDIR = sys.path[0]

_logger = logging.getLogger(__name__)


class MessageRoleSetModal(modal.Modal):
    def __init__(
        self,
        cog: "MessageRole",
        *,
        default_regex: str | None = None,
        default_grant: bool = True,
        default_roles: Sequence[nextcord.Role | int] | None = None,
        has_deleted_roles: bool = False,
    ) -> None:
        super().__init__("メッセージロールの設定", timeout=None)

        self.cog = cog

        self.regex = modal.ModalLabel(
            text="判定するメッセージ (正規表現)",
            component=modal.ModalTextInput(
                placeholder="判定したいメッセージを正規表現で入力してください",
                default_value=default_regex,
                max_length=128,
                required=True,
            ),
        )
        self.action_type = modal.ModalLabel(
            text="動作モード",
            component=modal.ModalStringSelect(
                placeholder="モードを選択してください",
                options=[
                    nextcord.SelectOption(
                        label="ロールを付与する",
                        value="grant",
                        default=default_grant,
                    ),
                    nextcord.SelectOption(
                        label="ロールを剥奪する",
                        value="revoke",
                        default=not default_grant,
                    ),
                ],
                required=True,
            ),
        )
        self.roles = modal.ModalLabel(
            text="付与/剥奪するロール (5個まで)",
            description=(
                "利用できなくなった一部のロールは一覧から削除されています。"
                if has_deleted_roles
                else None
            ),
            component=modal.ModalRoleSelect(
                placeholder="ロールを選択してください",
                default_values=default_roles,
                max_values=5,
                required=True,
            ),
        )

        self.add_item(self.regex)
        self.add_item(self.action_type)
        self.add_item(self.roles)

    def with_default_from_input(self) -> Self:
        return self.__class__(
            self.cog,
            default_regex=self.regex.component.value,
            default_grant=self.action_type.component.options[0].default,
            default_roles=self.roles.component.values.roles or None,
        )

    async def callback(self, interaction: Interaction) -> None:
        assert interaction.guild and isinstance(
            interaction.channel, nextcord.abc.GuildChannel | nextcord.Thread
        )

        await interaction.response.defer(ephemeral=True)

        try:
            regex = self.regex.component.value
            assert regex
            action_type = self.action_type.component.values[0] == "grant"
            roles = self.roles.component.values.roles

            try:
                _ = re.compile(regex)
            except Exception as e:
                await interaction.send(
                    embed=nextcord.Embed(
                        title="エラー",
                        description=f"入力された正規表現が不正です。\n```\n{e}```",
                        color=self.cog.bot.color.RED,
                    ),
                    view=MessageRoleSetRetryView(self.with_default_from_input()),
                    ephemeral=True,
                )
                return

            await self.cog.collection.update_one(
                {
                    "guild_id": interaction.guild.id,
                    "channel_id": interaction.channel.id,
                },
                {
                    "$set": {
                        "regex": regex,
                        "role_id": [r.id for r in roles],
                        "action_type": action_type,
                    }
                },
                upsert=True,
            )

            roles_desc = "、".join(r.mention for r in roles[:-1])
            roles_desc = f"{roles_desc and f'{roles_desc}と'}{roles[-1].mention}"
            await interaction.send(
                embed=nextcord.Embed(
                    title="メッセージロールの設定",
                    description=(
                        f"チャンネル:{interaction.channel.mention}\n"
                        f"判定メッセージ:`{regex}`\n"
                        f"ロール:{roles_desc}を{'付与' if action_type else '剥奪'}します。"
                    ),
                    color=0x00FF00,
                ),
                allowed_mentions=nextcord.AllowedMentions.none(),
                ephemeral=True,
            )

        except Exception:
            _logger.exception("An error has occurred when setting message role")
            await interaction.send(
                f"申し訳ございません。エラーが発生しました。\n```\n{self.cog.bot.format_exc()}```",
                ephemeral=True,
            )


class MessageRoleSetRetryView(nextcord.ui.View):
    def __init__(self, modal: MessageRoleSetModal) -> None:
        super().__init__(timeout=900)
        self.add_item(MessageRoleSetRetryButton(modal))


class MessageRoleSetRetryButton(nextcord.ui.Button):
    def __init__(self, modal: MessageRoleSetModal) -> None:
        super().__init__(
            style=nextcord.ButtonStyle.green,
            label="やり直す",
            emoji="\N{RIGHTWARDS ARROW WITH HOOK}",
        )
        self.modal = modal

    async def callback(self, interaction: Interaction) -> None:
        await interaction.response.send_modal(self.modal)


class MessageRole(commands.Cog):
    def __init__(self, bot: NIRA):
        self.bot = bot
        self.collection: motor_asyncio.AsyncIOMotorCollection = self.bot.database[
            "message_role"
        ]

    @nextcord.slash_command(name="mesrole", description="Message role command")
    async def slash_message_role(self, interaction: Interaction):
        pass

    @application_checks.has_permissions(manage_roles=True)
    @application_checks.guild_only()
    @slash_message_role.subcommand(
        name="set", description="チャンネルのメッセージロールの設定をします"
    )
    async def slash_message_role_set(self, interaction: Interaction):
        assert interaction.guild and interaction.channel

        data = await self.collection.find_one(
            {"guild_id": interaction.guild.id, "channel_id": interaction.channel.id}
        )
        roles = []
        has_deleted_roles = False
        if data and (role_ids := data["role_id"]):
            if not isinstance(role_ids, list):  # 旧フォーマット (単一ロール設定)
                role_ids = (role_ids,)

            for role_id in role_ids:
                if role := interaction.guild.get_role(role_id):
                    # 旧スラッシュコマンドでは@everyoneを選択することができた
                    # (もちろん正常に動作しないが)
                    # モーダルのRole Selectでは選択できないため除外しておく
                    if role.name != "@everyone":
                        roles.append(role)
                else:
                    has_deleted_roles = True

        await interaction.response.send_modal(
            MessageRoleSetModal(
                self,
                default_regex=data and data["regex"],
                default_grant=data["action_type"] if data else True,
                default_roles=roles or None,
                has_deleted_roles=has_deleted_roles,
            )
        )

    @application_checks.has_permissions(manage_roles=True)
    @application_checks.guild_only()
    @slash_message_role.subcommand(
        name="del", description="チャンネルのメッセージロールの設定を削除します"
    )
    async def slash_message_role_del(self, interaction: Interaction):
        assert (
            interaction.guild
            and interaction.channel
            and isinstance(interaction.user, nextcord.Member)
        )

        await interaction.response.defer(ephemeral=True)

        if not admin_check.admin_check(interaction.guild, interaction.user):
            await interaction.followup.send(
                embed=nextcord.Embed(
                    title="Error",
                    description="あなたは管理者ではありません。",
                    color=0xFF0000,
                )
            )
            return

        result = await self.collection.delete_one(
            {"guild_id": interaction.guild.id, "channel_id": interaction.channel.id}
        )

        if result.deleted_count == 0:
            await interaction.followup.send(
                embed=nextcord.Embed(
                    title="メッセージロールの設定",
                    description="このサーバーにはメッセージロールの設定がありません。",
                    color=0xFF0000,
                )
            )
        else:
            await interaction.followup.send(
                embed=nextcord.Embed(
                    title="メッセージロールの設定",
                    description=(
                        f"チャンネル:<#{interaction.channel.id}>\n"
                        "メッセージロールの設定を削除しました。"
                    ),
                    color=0x00FF00,
                )
            )

    @application_checks.has_permissions(manage_roles=True)
    @application_checks.guild_only()
    @slash_message_role.subcommand(
        name="list", description="メッセージロールの設定を表示します"
    )
    async def slash_message_role_list(self, interaction: Interaction):
        assert (
            interaction.guild
            and interaction.channel
            and isinstance(interaction.user, nextcord.Member)
        )

        await interaction.response.defer(ephemeral=True)
        if not admin_check.admin_check(interaction.guild, interaction.user):
            await interaction.followup.send(
                embed=nextcord.Embed(
                    title="Error",
                    description="あなたは管理者ではありません。",
                    color=0xFF0000,
                )
            )
            return

        mesroledatas = await self.collection.find(
            {"guild_id": interaction.guild.id}
        ).to_list(length=None)

        if len(mesroledatas) == 0:
            await interaction.followup.send(
                embed=nextcord.Embed(
                    title="メッセージロールの設定",
                    description="このサーバーにはメッセージロールの設定がありません。",
                    color=0x00FF00,
                )
            )
        else:
            embed = nextcord.Embed(
                title="メッセージロールの設定",
                description=interaction.guild.name,
                color=0x00FF00,
            )
            for mesroledata in mesroledatas:
                channel = await self.bot.fetch_channel(mesroledata["channel_id"])
                assert isinstance(channel, nextcord.abc.GuildChannel | nextcord.Thread)

                role_ids = mesroledata["role_id"]
                if not isinstance(role_ids, list):  # 旧フォーマット
                    role_ids = (role_ids,)
                roles_desc = "、".join(f"<@&{rid}>" for rid in role_ids[:-1])
                roles_desc = f"{roles_desc and f'{roles_desc}と'}<@&{role_ids[-1]}>"

                embed.add_field(
                    name=channel.name,
                    value=(
                        f"判定メッセージ:`{mesroledata['regex']}`\n"
                        f"ロール:{roles_desc}\n"
                        f"ロール{'付与' if mesroledata['action_type'] else '剥奪'}をします。"
                    ),
                    inline=False,
                )
            await interaction.followup.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message):
        if not isinstance(message.channel, nextcord.abc.GuildChannel | nextcord.Thread):
            return
        if message.author.bot:
            return
        assert message.guild and isinstance(message.author, nextcord.Member)

        result = await self.collection.find_one(
            {"guild_id": message.guild.id, "channel_id": message.channel.id}
        )
        if result is None:
            return
        try:
            m = re.search(result["regex"], message.content)
        except Exception:
            return
        if m is not None:
            role_ids = result["role_id"]
            roles = [
                role
                for role_id in (role_ids if isinstance(role_ids, list) else (role_ids,))
                if (role := message.guild.get_role(role_id))
                and role.name != "@everyone"
            ]
            if not roles:
                return
            if result["action_type"]:
                await message.author.add_roles(
                    *roles,
                    reason="nira-bot MessageRole Service",
                )
            else:
                await message.author.remove_roles(
                    *roles,
                    reason="nira-bot MessageRole Service",
                )
            await message.add_reaction("\u2705")

    @commands.command(
        name="mesrole",
        help="""\
指定された文章を含むメッセージが送信された場合にロールの付与/剥奪を行います。

・使い方
`/mesrole set`
`/mesrole del`
`/mesrole list`

※コンテキストコマンド`n!mesrole`は廃止されました。スラッシュコマンドをご使用ください。

・`/mesrole set`の設定項目
`[判定するメッセージ]`
実際に反応するメッセージです。
メッセージには[正規表現](https://qiita.com/tossh/items/635aea9a529b9deb3038)をご使用いただけます。

`[動作モード]`
ロールを付与するか、剥奪するかを指定します。

`[付与/剥奪するロール]`
実際に付与/剥奪するロールです。
5つまで設定可能です。

・設定例
判定するメッセージ: `I don't want to be ([に|ニ|ni]|[ら|ラ|ra])BOT`
動作モード: `ロールを剥奪する`
付与/剥奪するロール: `にら民`
""",
    )
    async def mesrole(self, ctx: commands.Context) -> None:
        await ctx.reply(
            embed=nextcord.Embed(
                title="エラー",
                description=(
                    f"コンテキストコマンド`{ctx.prefix}mesrole [set/del/list]`は廃止されました。\n"
                    "スラッシュコマンド`/mesrole [set/del/list]`をご使用ください。"
                ),
                color=self.bot.color.RED,
            ),
        )


def setup(bot):
    bot.add_cog(MessageRole(bot))
