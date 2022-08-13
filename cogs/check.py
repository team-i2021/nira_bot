import sys

import nextcord
from nextcord import Interaction
from nextcord.ext import commands

from util import admin_check, n_fc, eh, slash_tool

# 管理者かどうかをチェックする


class check(commands.Cog):
    def __init__(self, bot: commands.Bot, **kwagrs):
        self.bot = bot

    @nextcord.user_command(name="管理者権限チェック", guild_ids=n_fc.GUILD_IDS)
    async def admin_user(self, interaction: Interaction, member: nextcord.Member):
        if admin_check.admin_check(member.guild, member):
            await slash_tool.messages.mreply(interaction, "", embed=nextcord.Embed(title="ADMIN", description=f"権限があるようです。", color=0x00ff00))
        elif member.id in n_fc.py_admin:
            await slash_tool.messages.mreply(interaction, "", embed=nextcord.Embed(title="ADMIN", description=f"サーバー権限はありませんが、コマンドは実行できます。（BOT開発者）", color=0xffff00))
        else:
            await slash_tool.messages.mreply(interaction, "", embed=nextcord.Embed(title="ADMIN", description=f"権限がないようです。\n**（管理者権限を付与したロールがありませんでした。）**\n自分が管理者の場合は、自分に管理者権限を付与したロールを付けてください。", color=0xff0000))
        return

    @nextcord.slash_command(name="admin", description="管理者権限チェック", guild_ids=n_fc.GUILD_IDS)
    async def admin_slash(self, interaction: Interaction):
        if admin_check.admin_check(interaction.guild, interaction.user):
            await slash_tool.messages.mreply(interaction, "", embed=nextcord.Embed(title="ADMIN", description=f"権限があるようです。", color=0x00ff00))
        elif interaction.user.id in n_fc.py_admin:
            await slash_tool.messages.mreply(interaction, "", embed=nextcord.Embed(title="ADMIN", description=f"サーバー権限はありませんが、コマンドは実行できます。（BOT開発者）", color=0xffff00))
        else:
            await slash_tool.messages.mreply(interaction, "", embed=nextcord.Embed(title="ADMIN", description=f"権限がないようです。\n**（管理者権限を付与したロールがありませんでした。）**\n自分が管理者の場合は、自分に管理者権限を付与したロールを付けてください。", color=0xff0000))
        return

    @commands.command(name="admin", help="あなたが管理者権限があるかどうかを確認するだけです。")
    async def admin(self, ctx: commands.Context):
        if admin_check.admin_check(ctx.guild, ctx.author):
            await slash_tool.messages.mreply(ctx, "", embed=nextcord.Embed(title="ADMIN", description=f"権限があるようです。", color=0x00ff00))
        elif (await self.bot.is_owner(ctx.author)):
            await slash_tool.messages.mreply(ctx, "", embed=nextcord.Embed(title="ADMIN", description=f"サーバー権限はありませんが、コマンドは実行できます。（BOT開発者）", color=0xffff00))
        else:
            await slash_tool.messages.mreply(ctx, "", embed=nextcord.Embed(title="ADMIN", description=f"権限がないようです。\n**（管理者権限を付与したロールがありませんでした。）**\n自分が管理者の場合は、自分に管理者権限を付与したロールを付けてください。", color=0xff0000))
        return


def setup(bot, **kwargs):
    bot.add_cog(check(bot, **kwargs))
