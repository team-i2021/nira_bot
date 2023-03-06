import nextcord
from nextcord.ext import application_checks, commands
from nextcord.utils import get

from util import n_fc

# ユーザーがそのサーバーで管理者権限を持っているか確認する。


def admin_check(guild: nextcord.Message.guild, memb: nextcord.Member) -> bool:
    role_list = []
    if memb.id in n_fc.py_admin:
        return True
    if memb.id == guild.owner_id:
        return True
    for role in memb.roles:
        role_list.append(role.id)
    for i in range(len(role_list)):
        role = get(guild.roles, id=role_list[i])
        if (role.permissions).administrator:
            return True
    return False


def admin_only_cmd():
    async def extended_check(ctx: commands.Context) -> bool:
        return (await ctx.bot.is_owner(ctx.author)
                or (ctx.guild is not None and ctx.author.id == ctx.guild.owner_id)
                or await commands.has_permissions(administrator=True).predicate(ctx))
    return commands.check(extended_check)


def admin_only_app():
    async def extended_check(intr: nextcord.Interaction) -> bool:
        is_owner = False
        try:
            is_owner = await application_checks.is_owner().predicate(intr)
        except application_checks.ApplicationNotOwner:
            pass
        return (is_owner
                or (intr.guild is not None and intr.user.id == intr.guild.owner_id)
                or application_checks.has_permissions(administrator=True).predicate(intr))
    return application_checks.check(extended_check)
