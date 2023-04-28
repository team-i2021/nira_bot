import asyncio
import datetime
import logging
import traceback

import nextcord
from nextcord.ext import commands

from motor import motor_asyncio

from util.nira import NIRA


# ユーザー参加時の挙動


class UserJoin(commands.Cog):
    def __init__(self, bot: NIRA, **kwargs):
        self.bot = bot
        self.winfo_collection: motor_asyncio.AsyncIOMotorCollection = self.bot.database["welcome_info"]
        self.rk_collection: motor_asyncio.AsyncIOMotorCollection = self.bot.database["role_keeper"]
        self.invite_collection: motor_asyncio.AsyncIOMotorCollection = self.bot.database["invite_data"]
        asyncio.ensure_future(self.fetch_role_keeper())

    async def fetch_role_keeper(self):
        await self.bot.wait_until_ready()

        for guild in self.bot.guilds:
            rolekeeper = await self.rk_collection.find_one({"guild_id": guild.id})
            if guild.id not in rolekeeper:
                rolekeeper = {"rk": 0}
            for member in guild.members:
                rolekeeper[str(member.id)] = [role.id for role in member.roles if role.id != guild.id]
            asyncio.ensure_future(self.rk_collection.update_one({"guild_id": guild.id}, {"$set": rolekeeper}, upsert=True))

    @commands.Cog.listener()
    async def on_member_join(self, member: nextcord.Member):
        welcomeinfo = await self.winfo_collection.find_one({"guild_id": member.guild.id})
        rolekeeper = await self.rk_collection.find_one({"guild_id": member.guild.id})
        invites = await self.invite_collection.find_one({"guild_id": member.guild.id})

        if welcomeinfo is None:
            channel = None

        try:
            channel = member.guild.get_channel(welcomeinfo["channel_id"])
            if rolekeeper is None:
                rolekeeper = {"rk": False}
                for i in range(len(member.guild.members)):
                    if member.guild.members[i].id != member.id:
                        rolekeeper[member.guild.members[i].id] = [j.id for j in member.guild.members[i].roles if j.id != member.guild.id]
                asyncio.ensure_future(self.rk_collection.update_one({"guild_id": member.guild.id}, {"$set": rolekeeper}, upsert=True))
        except Exception as err:
            logging.error(err, traceback.format_exc())

        try:
            if member.id not in rolekeeper:
                # ロールキーパーデータにない場合
                embed = nextcord.Embed(
                    title="こんにちは！",
                    description=f"名前： `{member.name}`\nID: `{member.id}`",
                    color=0x00ff00
                )
            else:
                # ロールキーパーデータにある場合
                embed = nextcord.Embed(
                    title="あれ、また会った？",
                    description=f"名前： `{member.name}`\nID: `{member.id}`",
                    color=0x00ff00
                )

            if member.avatar is not None:
                embed.set_thumbnail(url=member.avatar.url)

            embed.add_field(
                name="アカウント製作日",
                value=f"```{member.created_at}```"
            )
            embed.add_field(
                name="現在のユーザー数",
                value=f"`{len(member.guild.members)}`人"
            )
        except Exception as err:
            logging.error(err, traceback.format_exc())

        try:
            Invites = await member.guild.invites()
            if invites is None:
                invites = {i.url: [None, i.uses] for i in Invites}
            else:
                invitedUrl = None
                for key, value in invites.items():
                    for i in Invites:
                        if i.url == key and i.uses != value[1]:
                            invitedUrl = i
                            invites[invitedUrl.url][1] = invitedUrl.uses
                            break
                invitedFrom = f"[{invites[invitedUrl.url][0]}]({invitedUrl.url})"
                if invites[invitedUrl.url][0] is None:
                    invitedFrom = f"[{invitedUrl.url}]({invitedUrl.url})"
                embed.add_field(
                    name="招待リンク",
                    value=f"{invitedFrom}から招待を受けました！",
                    inline=False
                )
            asyncio.ensure_future(self.invite_collection.update_one({"guild_id": member.guild.id}, {"$set": invites}, upsert=True))

        except Exception as err:
            logging.error(f"{err}\n{traceback.format_exc()}")

        try:
            if channel is not None:
                members_message = await channel.send(embed=embed)
            else:
                members_message = None

        except Exception as err:
            logging.error(err)

        await asyncio.sleep(3)

        if rolekeeper["rk"]:
            try:
                if member.id in rolekeeper:
                    for i in range(len(rolekeeper[member.id])):
                        role = member.guild.get_role(rolekeeper[member.id][i])
                        if role is not None: await member.add_roles(role)

                    embed.add_field(
                        name="付与済みロール",
                        value=f"{' '.join([f'<@&{i}>' for i in rolekeeper[member.id]])}"
                    )
                    if members_message is not None: await members_message.edit(embed=embed)

            except Exception as err:
                if members_message is not None: await members_message.edit(f"ロール付与時に何かしらのエラーが発生しました。\n何度も発生する場合はお問い合わせください。\n`{err}`", embed=embed)
                logging.error(err)


    @commands.Cog.listener()
    async def on_member_remove(self, member: nextcord.Member):
        leave_time = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
        join_time = member.joined_at
        time_diff: datetime.timedelta = leave_time - join_time
        time_diff = time_diff.total_seconds()
        user_id = member.id
        try:
            welcomeinfo = await self.winfo_collection.find_one({"guild_id": member.guild.id})

            user = await self.bot.fetch_user(user_id)
            if welcomeinfo is not None:
                channel = self.bot.get_channel(welcomeinfo["channel_id"])
            else:
                channel = None

            embed = nextcord.Embed(
                title="またどこかで！",
                description=f"名前: `{user.name}`\nID: `{user.id}`",
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
                if member.roles[i].id != member.guild.id:
                    role_text = role_text + f" <@&{member.roles[i].id}> "
                    role_ids.append(member.roles[i].id)
            if role_text != "":
                embed.add_field(name="付与されていたロール", value=f"{role_text}")
            if time_diff <= 100:
                embed.add_field(name="即抜けRTA記録", value=f"`{round(time_diff, 4)}`秒")
            if channel is not None: removed_message = await channel.send(embed=embed)

            # After send...

            rolekeeper = await self.rk_collection.find_one({"guild_id": member.guild.id})

            if rolekeeper is None:
                rolekeeper = {"rk": 0}
                return
            rolekeeper[member.id] = role_ids
            await self.rk_collection.update_one({"guild_id": member.guild.id}, {"$set": rolekeeper}, upsert=True)
            return
        except Exception as err:
            if channel is not None: await removed_message.edit(f"おっと...これは大変ですね...\nユーザー離脱時の処理時にエラーが発生しました。\n`{err}`", embed=embed)
            logging.error(f"ユーザー離脱時の情報表示システムのエラー\n{err}\n`{traceback.format_exc()}`")
            return


def setup(bot, **kwargs):
    bot.add_cog(UserJoin(bot, **kwargs))

