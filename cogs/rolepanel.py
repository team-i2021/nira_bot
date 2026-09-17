import logging
import re
import traceback
from collections.abc import Sequence

import nextcord
from nextcord import Interaction
from nextcord.ext import commands

from util import modal
from util.admin_check import admin_check
from util.nira import NIRA

_logger = logging.getLogger(__name__)

rolepanel_compile = re.compile(r"[0-9]+: <@&[0-9]+>")

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
        if message.author.id != self.bot.user.id:
            await interaction.response.send_message(
                embed=nextcord.Embed(
                    title="エラー",
                    description=f"{self.bot.user.mention}が送信したロールパネルにのみこのコマンドを使用できます。",
                    color=0xFF0000,
                ),
                ephemeral=True,
            )
            return
        if (message.content != "" or message.content is None) or (
            message.embeds == [] or len(message.embeds) > 1
        ):
            await interaction.response.send_message(
                embed=nextcord.Embed(
                    title="エラー",
                    description=f"""\
選択されたメッセージはロールパネルではないです。
(ロールパネルであるにもかかわらずこのメッセージが表示される場合はお問い合わせください。)

・エラーコード
`Reject reason: E1-{[message.content != "", message.content is None, message.embeds == [], len(message.embeds) > 1]}`""",
                    color=0xFF0000,
                ),
                ephemeral=True,
            )
            return
        # await interaction.response.defer(ephemeral=True)
        roles = []
        ErrorRole = []
        has_deleted_roles = False
        for i in range(len(message.embeds[0].description.splitlines())):
            content = message.embeds[0].description.splitlines()[i]
            if re.fullmatch(rolepanel_compile, content) is None:
                await interaction.response.send_message(
                    embed=nextcord.Embed(
                        title="エラー",
                        description=f"""\
選択されたメッセージはロールパネルではないです。
(ロールパネルであるにもかかわらずこのメッセージが表示される場合はお問い合わせください。)

・エラーコード
`Reject reason: E2-{i}`""",
                        color=0xFF0000,
                    ),
                    ephemeral=True,
                )
                return
            roleText = (
                re.sub("[0-9]+: ", "", content).replace("<@&", "").replace(">", "")
            )
            try:
                if role := interaction.guild.get_role(int(roleText)):
                    roles.append(role)
                else:
                    has_deleted_roles = True
            except Exception:
                ErrorRole.append(roleText)
        if ErrorRole != []:
            await interaction.user.send(
                embed=nextcord.Embed(
                    title="にらBOT ロールパネル 警告",
                    description=(
                        "下記ロール名またはIDは、エラーのために取得されませんでした。\n"
                        "恐れ入りますが、ロールの存在や権限設定を確認してから、再度やり直してください。\n"
                        "```\n"
                    )
                    + "\n".join(ErrorRole)
                    + "```",
                    color=0xFFFF00,
                )
            )
        await interaction.response.send_modal(
            RolePanelModal(
                message=message,
                default_title=message.embeds[0].title,
                default_roles=roles or None,
                has_deleted_roles=has_deleted_roles,
            )
        )

    @nextcord.slash_command(
        name="rolepanel",
        description="Create rolepanel",
        description_localizations={nextcord.Locale.ja: "ロールパネルを設置します"},
    )
    async def rolepanel_slash(self, interaction: Interaction):
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
    async def rolepanel(self, ctx: commands.Context):
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
