import nextcord
from nextcord.utils import get

from util import n_fc

#ユーザーがそのサーバーで管理者権限を持っているか確認する。


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
