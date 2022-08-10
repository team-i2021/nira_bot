import asyncio
import datetime
import json
import logging
import re
import sys
import traceback
from time import timezone

import HTTP_db
import nextcord
from nextcord.ext import commands

from util import admin_check, n_fc, eh, database, dict_list
from util.nira import NIRA


# ユーザー参加時の挙動


class RoleKeeper:
    name = "role_kepper"
    value = {}
    default = {}
    value_type = database.CHANNEL_VALUE


class WelcomeInfo:
    name = "welcome_info"
    value = {}
    default = {}
    value_type = database.GUILD_VALUE


class InviteData:
    name = "invite_data"
    value = {}
    default = {}
    value_type = database.CHANNEL_VALUE


class user_join(commands.Cog):
    def __init__(self, bot: NIRA, **kwargs):
        self.bot = bot
        asyncio.ensure_future(self.fetch_role_keeper())

    async def fetch_role_keeper(self):
        await self.bot.wait_until_ready()
        await database.default_pull(self.bot.client, RoleKeeper)

        for i in self.bot.guilds:
            if i.id not in RoleKeeper.value:
                RoleKeeper.value[i.id] = {"rk": 0}
            for j in i.members:
                RoleKeeper.value[i.id][j.id] = [k.id for k in j.roles if k.id != i.id]

        await database.default_push(self.bot.client, RoleKeeper)

    @commands.Cog.listener()
    async def on_member_join(self, member: nextcord.Member):
        await database.default_pull(self.bot.client, WelcomeInfo)
        await database.default_pull(self.bot.client, RoleKeeper)
        await database.default_pull(self.bot.client, InviteData)
        try:
            channel = member.guild.get_channel(WelcomeInfo.value[member.guild.id])
            if member.guild.id not in RoleKeeper.value:
                RoleKeeper.value[member.guild.id] = {"rk": 0}
                for i in range(len(member.guild.members)):
                    if member.guild.members[i].id != member.id:
                        RoleKeeper.value[member.guild.id][member.guild.members[i].id] = [j.id for j in member.guild.members[i].roles if j.id != member.guild.id]
                asyncio.ensure_future(database.default_push(self.bot.client, WelcomeInfo))
        except Exception as err:
            logging.error(err, traceback.format_exc())

        try:
            if member.id not in RoleKeeper.value[member.guild.id]:
                embed = nextcord.Embed(
                    title="こんにちは！",
                    description=f"名前： `{member.name}`\nID: `{member.id}`",
                    color=0x00ff00
                )
            else:
                embed = nextcord.Embed(
                    title="あれ、また会った？",
                    description=f"名前： `{member.name}`\nID: `{member.id}`",
                    color=0x00ff00
                )

            if member.avatar is not None:
                embed.set_thumbnail(url=member.avatar.url)
            embed.add_field(name="アカウント製作日",
                            value=f"```{member.created_at}```")
            embed.add_field(name="現在のユーザー数",
                            value=f"`{len(member.guild.members)}`人")
        except Exception as err:
            logging.error(err, traceback.format_exc())

        try:
            Invites = await member.guild.invites()
            if member.guild.id not in InviteData.value:
                InviteData.value[member.guild.id] = {i.url: [None, i.uses] for i in Invites}
            else:
                invitedUrl = None
                for key, value in InviteData.value[member.guild.id].items():
                    for i in Invites:
                        if i.url == key:
                            if i.uses != value[1]:
                                invitedUrl = i
                                InviteData.value[member.guild.id][invitedUrl.url][1] = invitedUrl.uses
                                break
                invitedFrom = f"[{InviteData.value[member.guild.id][invitedUrl.url][0]}]({invitedUrl.url})"
                if InviteData.value[member.guild.id][invitedUrl.url][0] is None:
                    invitedFrom = f"[{invitedUrl.url}]({invitedUrl.url})"
                embed.add_field(
                    name="招待リンク", value=f"{invitedFrom}から招待を受けました！", inline=False)
            asyncio.ensure_future(database.default_push(self.bot.client, InviteData))
        except Exception as err:
            logging.error(f"{err}\n{traceback.format_exc()}")

        try:
            if member.guild.id in WelcomeInfo.value and channel is not None:
                members_message = await channel.send(embed=embed)
            else:
                members_message = None

        except Exception as err:
            logging.error(err)
        await asyncio.sleep(2)

        if RoleKeeper.value[member.guild.id]["rk"] == 1:

            try:
                if member.id not in RoleKeeper.value[member.guild.id]:
                    RoleKeeper.value[member.guild.id][member.id] = [i.id for i in member.roles if i.id != member.guild.id]
                    asyncio.ensure_future(database.default_push(self.bot.client, RoleKeeper))
                else:
                    for i in range(len(RoleKeeper.value[member.guild.id][member.id])):
                        role = member.guild.get_role(RoleKeeper.value[member.guild.id][member.id][i])
                        if role is not None: await member.add_roles(role)

                    embed.add_field(
                        name="付与済みロール",
                        value=f"{' '.join([f'<@&{i}>' for i in RoleKeeper.value[member.guild.id][member.id]])}"
                    )
                    await members_message.edit(embed=embed)

            except Exception as err:
                await members_message.edit(f"ロール付与時に何かしらのエラーが発生しました。\n何度も発生する場合はお問い合わせください。\n`{err}`", embed=embed)
                logging.error(err)
        return

    @commands.Cog.listener()
    async def on_member_remove(self, member: nextcord.Member):
        leave_time = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
        join_time = member.joined_at
        time_diff: datetime.timedelta = leave_time - join_time
        time_diff = time_diff.total_seconds()
        user_id = member.id
        try:
            await database.default_pull(self.bot.client, WelcomeInfo)
            user = await self.bot.fetch_user(user_id)
            if member.guild.id in WelcomeInfo.value:
                channel = self.bot.get_channel(WelcomeInfo.value[member.guild.id])
            else:
                channel = None
            embed = nextcord.Embed(
                title="また来てねー！",
                description=f"名前：`{user.name}`\nID：`{user.id}`",
                color=0x00ff00
            )
            if user.avatar is not None:
                embed.set_thumbnail(url=user.avatar.url)
            embed.add_field(
                name="現在のユーザー数",
                value=f"`{len(member.guild.members)}`人"
            )
            role_text = ""
            role_ids = []
            for i in range(len(member.roles)):
                if member.roles[i].id == member.guild.id:
                    pass
                else:
                    role_text = role_text + f" <@&{member.roles[i].id}> "
                    role_ids.append(member.roles[i].id)
            embed.add_field(name="付与されていたロール", value=f"{role_text}")
            if time_diff <= 100:
                embed.add_field(name="即抜けRTA記録", value=f"`{round(time_diff, 4)}`秒")
            if channel == None:
                pass
            else:
                removed_message = await channel.send(embed=embed)
            
            # After send...

            await database.default_pull(self.bot.client, RoleKeeper)
            if member.guild.id not in RoleKeeper:
                RoleKeeper.value[member.guild.id] = {"rk": 0}
                return
            RoleKeeper.value[member.guild.id][member.id] = role_ids
            await database.default_push(self.bot.client, RoleKeeper)
            return
        except Exception as err:
            if channel == None:
                pass
            else:
                await removed_message.edit(f"おっと...これは大変ですね...\nユーザー離脱時の処理時にエラーが発生しました。\n`{err}`", embed=embed)
            logging.error(f"ユーザー離脱時の情報表示システムのエラー\n{err}\n`{traceback.format_exc()}`")
            return


def setup(bot, **kwargs):
    bot.add_cog(user_join(bot, **kwargs))

