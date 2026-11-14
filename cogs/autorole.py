import logging
from collections.abc import Sequence

import nextcord
from motor import motor_asyncio
from nextcord import Interaction, Role
from nextcord.ext import application_checks, commands

from util import modal
from util.nira import NIRA

# Autorole

_logger = logging.getLogger(__name__)


class AutoRoleSetModal(modal.Modal):
    def __init__(
        self,
        cog: "autorole",
        *,
        default_roles: Sequence[Role | int] | None = None,
        has_deleted_roles: bool = False,
    ) -> None:
        super().__init__("自動ロールの設定", timeout=None)

        self.cog = cog

        self.roles = modal.ModalLabel(
            text="ユーザー加入時に付与するロール (5個まで)",
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

        self.add_item(self.roles)

    async def callback(self, interaction: Interaction) -> None:
        assert interaction.guild

        await interaction.response.defer(ephemeral=True)

        try:
            roles = self.roles.component.values.roles
            await self.cog.collection.update_one(
                {"guild_id": interaction.guild.id},
                {"$set": {"role_id": [r.id for r in roles]}},
                upsert=True,
            )

            roles_desc = "、".join(r.mention for r in roles[:-1])
            roles_desc = f"{roles_desc and f'{roles_desc}と'}{roles[-1].mention}"
            await interaction.send(
                embed=nextcord.Embed(
                    title="自動ロール",
                    description=f"設定完了：{roles_desc}を自動的に付与します。",
                    color=self.cog.bot.color.NORMAL,
                ),
                allowed_mentions=nextcord.AllowedMentions.none(),
                ephemeral=True,
            )

        except Exception:
            _logger.exception("An error has occurred when setting auto role")
            await interaction.send(
                f"申し訳ございません。エラーが発生しました。\n```\n{self.cog.bot.format_exc()}```",
                ephemeral=True,
            )


class autorole(commands.Cog):
    def __init__(self, bot: NIRA):
        self.bot = bot
        self.collection: motor_asyncio.AsyncIOMotorCollection = self.bot.database[
            "autorole"
        ]

    @nextcord.slash_command(name="autorole", description="自動ロール")
    async def autorole(self, interaction: Interaction):
        pass

    @commands.has_permissions(manage_roles=True)
    @commands.guild_only()
    @commands.command(
        name="autorole",
        aliases=("自動ロール", "オートロール"),
        help="""\
ユーザーが加入したときに、指定したロールを自動的に付与することが出来ます。

ロールは5つまで指定可能です。

・使い方
設定: `/autorole on` (モーダルウィンドウが開きます。)
無効化: `/autorole off`

※コンテキストコマンド`n!autorole`は廃止されました。スラッシュコマンドをご使用ください。
""",
    )
    async def autorole_ctx(self, ctx: commands.Context):
        await ctx.reply(
            embed=nextcord.Embed(
                title="エラー",
                description=(
                    f"コンテキストコマンド`{ctx.prefix}{ctx.invoked_with} [on/off]`は廃止されました。\n"
                    "スラッシュコマンド`/autorole [on/off/status]`をご使用ください。"
                ),
                color=self.bot.color.RED,
            ),
        )

    @application_checks.has_permissions(manage_roles=True)
    @application_checks.guild_only()
    @autorole.subcommand(name="off", description="自動ロールを無効にします")
    async def autorole_off(self, interaction: Interaction):
        assert interaction.guild

        await interaction.response.defer(ephemeral=True)

        result = await self.collection.delete_one({"guild_id": interaction.guild.id})
        if result.deleted_count == 0:
            desc = "サーバーで自動ロールは設定されていません。"
        else:
            desc = "サーバーで自動ロールを無効にしました。"

        await interaction.send(
            embed=nextcord.Embed(
                title="自動ロール",
                description=desc,
                color=self.bot.color.NORMAL,
            ),
            ephemeral=True,
        )

    @application_checks.has_permissions(manage_roles=True)
    @application_checks.guild_only()
    @autorole.subcommand(
        name="on", description="ユーザーが加入したときに自動的にロールを付与します"
    )
    async def autorole_on(self, interaction: Interaction):
        assert interaction.guild

        data = await self.collection.find_one({"guild_id": interaction.guild.id})
        roles = []
        has_deleted_roles = False
        if data and (role_ids := data["role_id"]):
            if not isinstance(role_ids, list):  # 旧フォーマット (単一ロール設定)
                role_ids = (role_ids,)

            for role_id in role_ids:
                if role := interaction.guild.get_role(role_id):
                    # 無いはずだが、念のため@everyoneチェック
                    if role.name != "@everyone":
                        roles.append(role)
                else:
                    has_deleted_roles = True

        await interaction.response.send_modal(
            AutoRoleSetModal(
                self,
                default_roles=roles or None,
                has_deleted_roles=has_deleted_roles,
            )
        )

    @application_checks.has_permissions(manage_roles=True)
    @application_checks.guild_only()
    @autorole.subcommand(name="status", description="自動ロールの設定状態を確認します")
    async def autorole_status(self, interaction: Interaction):
        assert interaction.guild

        await interaction.response.defer(ephemeral=True)

        data = await self.collection.find_one({"guild_id": interaction.guild.id})
        if data is not None:
            role_ids = data["role_id"]
            if not isinstance(role_ids, list):  # 旧フォーマット
                role_ids = (role_ids,)
            roles_desc = "、".join(f"<@&{rid}>" for rid in role_ids[:-1])
            roles_desc = f"{roles_desc and f'{roles_desc}と'}<@&{role_ids[-1]}>"
            desc = f"自動ロールは有効です。\n自動付与されるロールは{roles_desc}です。"
        else:
            desc = "自動ロールは無効です。"

        await interaction.send(
            embed=nextcord.Embed(
                title="自動ロール",
                description=desc,
                color=self.bot.color.NORMAL,
            ),
            allowed_mentions=nextcord.AllowedMentions.none(),
            ephemeral=True,
        )

    @commands.Cog.listener()
    async def on_member_join(self, member: nextcord.Member):
        result = await self.collection.find_one({"guild_id": member.guild.id})
        if result is not None:
            role_ids = result["role_id"]
            roles = [
                role
                for role_id in (role_ids if isinstance(role_ids, list) else (role_ids,))
                if (role := member.guild.get_role(role_id)) and role.name != "@everyone"
            ]
            if roles:
                await member.add_roles(*roles, reason="NiraBOT AutoRole")


def setup(bot):
    bot.add_cog(autorole(bot))
