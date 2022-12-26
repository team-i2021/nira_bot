import asyncio
import datetime
import logging
import os
import re
import sys
import traceback
from os import getenv

import nextcord
from nextcord import Interaction, SlashOption, Role
from nextcord.ext import commands

from util import n_fc, mc_status, database
from util.admin_check import admin_check
from util.nira import NIRA

rolepanel_compile = re.compile(r"[0-9]+: <@&[0-9]+>")

# RolePanel

class RolePanelSlashInput(nextcord.ui.Modal):
    def __init__(self, bot):
        super().__init__(
            "ロールパネル",
            timeout=None
        )

        self.bot = bot

        self.EmbedTitle = nextcord.ui.TextInput(
            label=f"ロールパネルのタイトル",
            style=nextcord.TextInputStyle.short,
            placeholder=f"こっからロールとってね",
            required=False
        )
        self.add_item(self.EmbedTitle)

        self.Roles = nextcord.ui.TextInput(
            label=f"ロールの名前又はID（ロールごとに改行！）",
            style=nextcord.TextInputStyle.paragraph,
            placeholder=f"にら民1\nにら民2\n1234567890",
            required=True
        )
        self.add_item(self.Roles)

    async def callback(self, interaction: Interaction) -> None:
        await interaction.response.defer()

        values = [i for i in self.Roles.value.splitlines() if i != ""]

        if len(values) > 25:
            await interaction.followup.send("ロールパネル機能は最大で24個まで選択肢を指定できます。")
            return

        embed_content = ""
        ViewArgs = []

        for i in range(len(values)):
            role_id = None
            try:
                role_id = int(values[i])
            except ValueError:
                roles = interaction.guild.roles
                for j in range(len(roles)):
                    if roles[j].name == values[i]:
                        role_id = roles[j].id
                        break
                if role_id == None:
                    await interaction.followup.send(f"`{values[i]}`という名前のロールは存在しません")
                    return
            if role_id == None:
                await interaction.followup.send(f"`{values[i]}`という名前のロールは存在しません")
                return
            embed_content += f"{i+1}: <@&{role_id}>\n"
            ViewArgs.append([i+1, role_id])

        embed_title = self.EmbedTitle.value
        if embed_title == "" or embed_title is None:
            embed_title = "にらBOTロールパネル"
        try:
            await interaction.followup.send(embed=nextcord.Embed(title=embed_title, description=embed_content, color=0x00ff00), view=RolePanelView(ViewArgs))
        except Exception:
            await interaction.followup.send(f"申し訳ございません。エラーが発生しました。\n```\n{traceback.format_exc()}```")
            return


class RolePanelEditModal(nextcord.ui.Modal):
    def __init__(self, bot, message, oldroles):
        super().__init__(
            "ロールパネル 編集",
            timeout=None
        )

        self.bot = bot
        self.message = message
        self.oldroles = oldroles

        self.Roles = nextcord.ui.TextInput(
            label=f"ロールの名前又はID（ロールごとに改行！）",
            style=nextcord.TextInputStyle.paragraph,
            placeholder=f"にら民1\nにら民2\n1234567890",
            required=True,
            default_value="\n".join(oldroles)
        )
        self.add_item(self.Roles)

    async def callback(self, interaction: Interaction) -> None:
        await interaction.response.defer(ephemeral=True)

        values = [i for i in self.Roles.value.splitlines() if i != ""]

        if len(values) > 25:
            await interaction.followup.send("ロールパネル機能は最大で24個まで選択肢を指定できます。")
            return

        embed_content = ""
        ViewArgs = []

        for i in range(len(values)):
            role_id = None
            try:
                role_id = int(values[i])
            except ValueError:
                roles = interaction.guild.roles
                for j in range(len(roles)):
                    if roles[j].name == values[i]:
                        role_id = roles[j].id
                        break
                if role_id == None:
                    await interaction.followup.send(f"`{values[i]}`という名前のロールが見つかりませんでした。")
                    return
            if role_id == None:
                await interaction.followup.send(f"`{values[i]}`という名前のロールが見つかりませんでした。")
                return
            embed_content += f"{i+1}: <@&{role_id}>\n"
            ViewArgs.append([i+1, role_id])

        EmbedTitle = self.message.embeds[0].title
        try:
            await self.message.edit(embed=nextcord.Embed(title=EmbedTitle, description=embed_content, color=0x00ff00), view=RolePanelView(ViewArgs))
        except Exception as err:
            await interaction.followup.send(f"エラー: `{err}`")
            return


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
            custom_id=f"RolePanel:{arg[1]}"
        )


class Rolepanel(commands.Cog):
    def __init__(self, bot: NIRA, **kwargs):
        self.bot = bot

    @nextcord.message_command(name="Edit Rolepanel", name_localizations={nextcord.Locale.ja: "ロールパネル編集"}, guild_ids=n_fc.GUILD_IDS)
    async def edit_rolepanel(self, interaction: Interaction, message: nextcord.Message):
        if not admin_check(interaction.guild, interaction.user):
            await interaction.response.send_message(embed=nextcord.Embed(title="エラー", description=f"管理者の方のみがこのコマンドを使用できます。", color=0xff0000), ephemeral=True)
            return
        if message.author.id != self.bot.user.id:
            await interaction.response.send_message(embed=nextcord.Embed(title="エラー", description=f"{self.bot.user.mention}が送信したロールパネルにのみこのコマンドを使用できます。", color=0xff0000), ephemeral=True)
            return
        if (message.content != "" or message.content is None) or (message.embeds == [] or len(message.embeds) > 1):
            await interaction.response.send_message(
                embed=nextcord.Embed(
                    title="エラー",
                    description=f"""\
選択されたメッセージはロールパネルではないです。
(ロールパネルであるにもかかわらずこのメッセージが表示される場合はお問い合わせください。)

・エラーコード
`Reject reason: E1-{[message.content != "", message.content is None, message.embeds == [], len(message.embeds) > 1]}`""",
                    color=0xff0000
                ),
                ephemeral=True
            )
            return
        # await interaction.response.defer(ephemeral=True)
        roles = []
        ErrorRole = []
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
                        color=0xff0000
                    ),
                    ephemeral=True
                )
                return
            roleText = re.sub(
                "[0-9]+: ", "", content).replace("<@&", "").replace(">", "")
            try:
                roles.append(interaction.guild.get_role(int(roleText)).name)
            except Exception:
                ErrorRole.append(roleText)
        if ErrorRole != []:
            await interaction.user.send(
                embed=nextcord.Embed(
                    title="にらBOT ロールパネル 警告",
                    description="下記ロール名またはIDは、エラーのために取得されませんでした。\n恐れ入りますが、ロールの存在や権限設定を確認してから、再度やり直してください。\n```\n" +
                    "\n".join(ErrorRole) + "```",
                    color=0xffff00
                )
            )
        await interaction.response.send_modal(RolePanelEditModal(self.bot, message, roles))

    @nextcord.slash_command(name="rolepanel", description="Create rolepanel", description_localizations={nextcord.Locale.ja: "ロールパネルを設置します"}, guild_ids=n_fc.GUILD_IDS)
    async def rolepanel_slash(
        self,
        interaction: Interaction
    ):
        if not admin_check(interaction.guild, interaction.user):
            await interaction.response.send_message(embed=nextcord.Embed(title="エラー", description=f"管理者のみがこのコマンドを使用できます。", color=0xff0000), ephemeral=True)
            return
        modal = RolePanelSlashInput(self.bot)
        await interaction.response.send_modal(modal=modal)
        return

    @commands.command(name="rolepanel", aliases=["ロールパネル", "rp", "ろーるぱねる", "ろーぱね"], help="""\
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
ただ、重複してのロール指定はできません。""")
    async def rolepanel(self, ctx: commands.Context):
        if not admin_check(ctx.guild, ctx.author):
            await ctx.send("あなたは管理者ではありません。")
            return
        if len(ctx.message.content.splitlines()) < 2:
            await ctx.send("ロールパネル機能を使用するにはメッセージ内容とロールIDまたは名前を指定してください。")
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
                if role_id == None:
                    await ctx.reply(f"エラー: 指定されたロール`{ctx.message.content.splitlines()[i]}`が存在しません。")
                    return
            if role_id == None:
                await ctx.reply(f"エラー: 指定されたロール`{ctx.message.content.splitlines()[i]}`が存在しません。")
                return
            embed_content += f"{i}: <@&{role_id}>\n"
            ViewArgs.append([i, role_id])
        try:
            await ctx.send(embed=nextcord.Embed(title=f"{content}", description=embed_content, color=0x00ff00), view=RolePanelView(ViewArgs))
        except Exception:
            await ctx.send(f"申し訳ございません。エラーが発生しました。\n```\n{traceback.format_exc()}```")
            return

    @commands.Cog.listener()
    async def on_interaction(self, interaction: Interaction) -> None:
        # amuseから借りパク
        if interaction.type is not nextcord.InteractionType.component:
            return

        custom_id = interaction.data.get("custom_id")
        if custom_id is None or not custom_id.startswith(f"RolePanel:"):
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
                    await interaction.send(f"`{role.name}`を剥奪しました。", ephemeral=True)
                    return
            await interaction.user.add_roles(role)
            await interaction.send(f"`{role.name}`を付与しました。", ephemeral=True)
            return
        except Exception as err:
            await interaction.send(f"ロール付与/剥奪時のエラー: {err}", ephemeral=True)



# args = [["ButtonLabel", "Role_Id"]]


def setup(bot, **kwargs):
    bot.add_cog(Rolepanel(bot, **kwargs))
