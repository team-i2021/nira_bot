import dataclasses
import logging
import re
import traceback
from collections.abc import Sequence

import nextcord
from nextcord import Interaction
from nextcord.ext import application_checks, commands

from util import modal
from util.admin_check import admin_check
from util.nira import NIRA

_logger = logging.getLogger(__name__)

pat_panel_role_str = re.compile(r"([0-9]+): <@&([0-9]+)>")

# RolePanel


class RolePanelModal(modal.Modal):
    def __init__(
        self,
        *,
        message: nextcord.Message | None = None,
        default_title: str | None = None,
        default_roles: Sequence[nextcord.Role | int] | None = None,
        has_deleted_roles: bool = False,
    ) -> None:
        super().__init__(f"ロールパネル{"編集" if message else "作成"}", timeout=None)

        self.message = message

        self.panel_title = modal.ModalLabel(
            text="ロールパネルのタイトル",
            component=modal.ModalTextInput(
                style=nextcord.TextInputStyle.short,
                placeholder="こっからロールとってね",
                default_value=default_title or "にらBOTロールパネル",
                required=True,
            ),
        )
        self.panel_roles = modal.ModalLabel(
            text="設定するロール (25個まで)",
            description=(
                "利用できなくなった一部のロールは一覧から削除されています。"
                if has_deleted_roles
                else None
            ),
            component=modal.ModalRoleSelect(
                placeholder="ロールを選択してください",
                default_values=default_roles,
                max_values=25,
                required=True,
            ),
        )

        self.add_item(self.panel_title)
        self.add_item(self.panel_roles)

    async def callback(self, interaction: Interaction) -> None:
        await interaction.response.defer(ephemeral=not self.message)

        embed_content = ""
        view_args: list[tuple[int, int]] = []

        for i, role in enumerate(self.panel_roles.component.values.roles):
            embed_content += f"{i + 1}: {role.mention}\n"
            view_args.append((i + 1, role.id))

        try:
            fn = self.message.edit if self.message else interaction.followup.send
            await fn(
                embed=nextcord.Embed(
                    title=self.panel_title.component.value,
                    description=embed_content,
                    color=0x00FF00,
                ),
                view=RolePanelView(view_args),
                allowed_mentions=nextcord.AllowedMentions.none(),
            )
        except Exception:
            _logger.exception(
                f"An error has occurred when {"editing" if self.message else "sending"} role panel"
            )
            await interaction.followup.send(
                f"申し訳ございません。エラーが発生しました。\n```\n{traceback.format_exc()}```"
            )


class RolePanelView(nextcord.ui.View):
    def __init__(self, args):
        super().__init__(timeout=None)

        for i in args:
            self.add_item(RolePanelButton(i))


class RolePanelButton(nextcord.ui.Button):
    def __init__(self, arg):
        super().__init__(
            label=arg[0],
            style=nextcord.ButtonStyle.green,
            custom_id=f"RolePanel:{arg[1]}",
        )


@dataclasses.dataclass(slots=True)
class _RolePanelRoles:
    roles: list[nextcord.Role]
    deleted_roles: list[int]


@dataclasses.dataclass(slots=True)
class _RolePanelParseErr:
    is_content_empty: bool = True
    num_of_embeds: int = 1
    embed_has_description: bool = True
    embed_description_invalid: tuple[int, re.Match[str] | str | None] | None = None

    def __bool__(self):
        return not (
            self.is_content_empty
            and self.num_of_embeds == 1
            and self.embed_has_description
            and self.embed_description_invalid is None
        )

    def error_code(self) -> str:
        if not self:
            return ""
        elif self.embed_description_invalid:
            return f"E2-{self.embed_description_invalid[0]}"
        else:
            values = (
                self.is_content_empty,
                self.num_of_embeds,
                self.embed_has_description,
            )
            return f"E1-{values}"


def _parse_rolepanel(message: nextcord.Message) -> _RolePanelRoles | _RolePanelParseErr:
    """ロールパネルメッセージを解析する"""

    assert message.guild

    err = _RolePanelParseErr(
        is_content_empty=not message.content,
        num_of_embeds=len(message.embeds),
    )
    if err:
        return err

    description = message.embeds[0].description
    if not description:
        err.embed_has_description = False
        return err

    roles: list[nextcord.Role] = []
    deleted_roles: list[int] = []
    for i, line in enumerate(description.splitlines()):
        if i >= 25:
            err.embed_description_invalid = (i, None)
            return err
        match = pat_panel_role_str.fullmatch(line)
        if not match:
            err.embed_description_invalid = (i, line)
            return err
        try:
            role_id = int(match.group(2))  # 正規表現上はエラーにならないはず...
            if role := message.guild.get_role(role_id):  # これも例外は出さないはず...
                roles.append(role)
            else:
                deleted_roles.append(role_id)
        except Exception:
            err.embed_description_invalid = (i, match)
            _logger.exception(f"Unexpected parsing error has occurred, {err=!r}")
            return err

    return _RolePanelRoles(roles, deleted_roles)


class Rolepanel(commands.Cog):
    def __init__(self, bot: NIRA):
        self.bot = bot
        self.add_role_mes = (
            "ロール「`{role_name}`」をあなたに追加しました！\n"
            "（もう一度同じボタンを押すと、ロール「`{role_name}`」を削除します。）"
        )
        self.remove_role_mes = (
            "ロール「`{role_name}`」をあなたから削除しました！\n"
            "（もう一度同じボタンを押すと、ロール「`{role_name}`」を追加します。）"
        )

    @nextcord.message_command(
        name="Edit Rolepanel",
        name_localizations={nextcord.Locale.ja: "ロールパネル編集"},
        contexts=[nextcord.InteractionContextType.guild],
    )
    @application_checks.guild_only()
    async def edit_rolepanel(self, interaction: Interaction, message: nextcord.Message):
        assert interaction.guild and isinstance(interaction.user, nextcord.Member)
        if not admin_check(interaction.guild, interaction.user):
            await interaction.response.send_message(
                embed=nextcord.Embed(
                    title="エラー",
                    description="管理者の方のみがこのコマンドを使用できます。",
                    color=0xFF0000,
                ),
                ephemeral=True,
            )
            return
        if message.author != self.bot.user:
            assert self.bot.user
            await interaction.response.send_message(
                embed=nextcord.Embed(
                    title="エラー",
                    description=f"{self.bot.user.mention}が送信したロールパネルにのみこのコマンドを使用できます。",
                    color=0xFF0000,
                ),
                ephemeral=True,
            )
            return

        result = _parse_rolepanel(message)
        if isinstance(result, _RolePanelParseErr):
            await interaction.response.send_message(
                embed=nextcord.Embed(
                    title="エラー",
                    description=f"""\
選択されたメッセージはロールパネルではないです。
(ロールパネルであるにもかかわらずこのメッセージが表示される場合はお問い合わせください。)

・エラーコード
`Reject reason: {result.error_code()}`""",
                    color=0xFF0000,
                ),
                ephemeral=True,
            )
            return

        await interaction.response.send_modal(
            RolePanelModal(
                message=message,
                default_title=message.embeds[0].title,
                default_roles=result.roles or None,
                has_deleted_roles=bool(result.deleted_roles),
            )
        )

    @nextcord.slash_command(
        name="rolepanel",
        description="Create rolepanel",
        description_localizations={nextcord.Locale.ja: "ロールパネルを設置します"},
        contexts=[nextcord.InteractionContextType.guild],
    )
    @application_checks.guild_only()
    async def rolepanel_slash(self, interaction: Interaction):
        assert interaction.guild and isinstance(interaction.user, nextcord.Member)
        if not admin_check(interaction.guild, interaction.user):
            await interaction.response.send_message(
                embed=nextcord.Embed(
                    title="エラー",
                    description="管理者のみがこのコマンドを使用できます。",
                    color=0xFF0000,
                ),
                ephemeral=True,
            )
            return
        modal = RolePanelModal()
        await interaction.response.send_modal(modal=modal)
        return

    @commands.command(
        name="rolepanel",
        aliases=["ロールパネル", "rp", "ろーるぱねる", "ろーぱね"],
        help="""\
ロールパネル機能

ボタンを押すことでロールを付与/削除するメッセージを送信します。
```
n!rolepanel [*メッセージ内容]
[ロール名又はID1]
[ロール名又はID2]
[ロール名又はID3]
...
```
`/rolepanel`

ロールは最大で25個まで指定できます。
ただ、重複してのロール指定はできません。""",
    )
    @commands.guild_only()
    async def rolepanel(self, ctx: commands.Context):
        assert ctx.guild and isinstance(ctx.author, nextcord.Member)
        if not admin_check(ctx.guild, ctx.author):
            await ctx.send("あなたは管理者ではありません。")
            return
        if len(ctx.message.content.splitlines()) < 2:
            await ctx.send(
                "ロールパネル機能を使用するにはメッセージ内容とロールIDまたは名前を指定してください。"
            )
            return
        elif len(ctx.message.content.splitlines()) > 26:
            await ctx.send("ロールパネル機能は最大で25個までロールを指定できます。")
            return
        args = ctx.message.content.splitlines()[0].split(" ", 1)
        if len(args) == 1:
            content = "にらBOT ロールパネル"
        else:
            content = args[1]
        ViewArgs = []
        embed_content = ""
        for i in range(len(ctx.message.content.splitlines())):
            if i == 0:
                continue
            role_id = None
            try:
                role_id = int(ctx.message.content.splitlines()[i])
            except ValueError:
                roles = ctx.guild.roles
                for j in range(len(roles)):
                    if roles[j].name == ctx.message.content.splitlines()[i]:
                        role_id = roles[j].id
                        break
                if role_id is None:
                    await ctx.reply(
                        f"エラー: 指定されたロール`{ctx.message.content.splitlines()[i]}`が存在しません。"
                    )
                    return
            if role_id is None:
                await ctx.reply(
                    f"エラー: 指定されたロール`{ctx.message.content.splitlines()[i]}`が存在しません。"
                )
                return
            embed_content += f"{i}: <@&{role_id}>\n"
            ViewArgs.append([i, role_id])
        try:
            await ctx.send(
                embed=nextcord.Embed(
                    title=f"{content}", description=embed_content, color=0x00FF00
                ),
                view=RolePanelView(ViewArgs),
            )
        except Exception:
            _logger.exception("An error has occurred")
            await ctx.send(
                f"申し訳ございません。エラーが発生しました。\n```\n{traceback.format_exc()}```"
            )
            return

    @commands.Cog.listener()
    async def on_interaction(self, interaction: Interaction) -> None:
        # amuseから借りパク
        if interaction.type is not nextcord.InteractionType.component:
            return
        if not interaction.guild:
            return

        assert interaction.data and isinstance(interaction.user, nextcord.Member)

        custom_id = interaction.data.get("custom_id")
        if custom_id is None or not custom_id.startswith("RolePanel:"):
            return

        role_id = None
        try:
            _, role_id = custom_id.split(":", 1)
            RoleId = int(role_id)
        except ValueError:
            return

        try:
            await interaction.response.defer(ephemeral=True)
        except Exception:
            pass

        try:
            role = interaction.guild.get_role(RoleId)
            if not role:
                await interaction.send(
                    embed=nextcord.Embed(
                        title="エラー",
                        description="このロールは既に削除されています。",
                        color=0xFF0000,
                    ),
                    ephemeral=True,
                )
                return
            for i in interaction.user.roles:
                if i == role:
                    await interaction.user.remove_roles(role)
                    await interaction.send(
                        self.remove_role_mes.format(role_name=role.name), ephemeral=True
                    )
                    return
            await interaction.user.add_roles(role)
            await interaction.send(
                self.add_role_mes.format(role_name=role.name), ephemeral=True
            )
            return
        except Exception as err:
            _logger.exception("An error has occurred")
            await interaction.send(
                "大変恐れ入りますが、エラーが発生しました。\n"
                "（BOTに適切な権限がないか、サーバーからロールが削除されているかもしれません。\n"
                "解決しない場合はBOT開発者へお問い合わせください。）",
                embed=nextcord.Embed(
                    title="エラー",
                    description=str(err),
                    color=0xFF0000,
                ),
                ephemeral=True,
            )


def setup(bot):
    bot.add_cog(Rolepanel(bot))
