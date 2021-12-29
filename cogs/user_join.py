from discord.ext import commands
import discord
import re
import sys
import json
from cogs.debug import save
from cogs.embed import embed
sys.path.append('../')
from util import admin_check, n_fc, eh

#loggingの設定
import logging
dir = sys.path[0]
class NoTokenLogFilter(logging.Filter):
    def filter(self, record):
        message = record.getMessage()
        return 'token' not in message

logger = logging.getLogger(__name__)
logger.addFilter(NoTokenLogFilter())
formatter = '%(asctime)s$%(filename)s$%(lineno)d$%(funcName)s$%(levelname)s:%(message)s'
logging.basicConfig(format=formatter, filename=f'{dir}/nira.log', level=logging.INFO)

#ユーザー参加時の挙動


class user_join(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        user_id = member.id
        try:
            user = await self.bot.fetch_user(user_id)
            if member.guild.id not in n_fc.welcome_id_list:
                return
            channel = self.bot.get_channel(n_fc.welcome_id_list[member.guild.id])
            embed = discord.Embed(title="Welcome!", description=f"名前：`{user.name}`\nID：`{user.id}`", color=0x00ff00)
            embed.set_thumbnail(url=f"https://cdn.discordapp.com/avatars/{user.id}/{str(user.avatar)}")
            embed.add_field(name="アカウント製作日", value=f"```{user.created_at}```")
            if member.guild.id not in n_fc.role_keeper:
                n_fc.role_keeper[member.guild.id] = {"rk":0}
                await channel.send(embed=embed)
                save()
                return
            if member.id not in n_fc.role_keeper[member.guild.id]:
                await channel.send(embed=embed)
                return
            role_list = n_fc.role_keeper[member.guild.id][member.id]
            for i in range(len(role_list)):
                role = member.guild.get_role(role_list[i])
                await member.add_roles(role)
            del n_fc.role_keeper[member.guild.id][member.id]
            role_text = ""
            for i in range(len(member.roles)):
                if member.roles[i].name != "@everyone":
                    role_text = role_text + f" <@&{member.roles[i].id}> "
            embed.add_field(name="ロールキーパー", value=f"ロールを付与しました。\n{role_text}")
            await channel.send(embed=embed)
            save()
            return
        except BaseException as err:
            if str(err) == "403 Forbidden (error code: 50001): Missing Access":
                embed.add_field(name="ロールキーパー発動時のエラー", value=f"にらBOTにロールを管理する権限がありません！やり直してください！\n・付与予定のロールIDリスト```{role_list}```")
                await channel.send(embed=embed)
                return
            elif str(err) == "403 Forbidden (error code: 50013): Missing Permissions":
                embed.add_field(name="ロールキーパー発動時のエラー", value=f"ロール「にらBOT」より上にあるロールを付与しようとしました！ロール設定を確認してください！\n・付与予定のロールIDリスト```{role_list}```")
                await channel.send(embed=embed)
                return
            logging.error(f"ユーザー加入時の情報表示システムのエラー\n{err}")
            return
    
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        user_id = member.id
        try:
            user = await self.bot.fetch_user(user_id)
            if member.guild.id not in n_fc.welcome_id_list:
                return
            channel = self.bot.get_channel(n_fc.welcome_id_list[member.guild.id])
            embed = discord.Embed(title="See ya...", description=f"名前：`{user.name}`\nID：`{user.id}`", color=0x00ff00)
            embed.set_thumbnail(url=f"https://cdn.discordapp.com/avatars/{user.id}/{str(user.avatar)}")
            role_text = ""
            role_ids = []
            for i in range(len(member.roles)):
                if member.roles[i].name == "@everyone":
                    role_text = role_text + f" {member.roles[i].name} "
                else:
                    role_text = role_text + f" <@&{member.roles[i].id}> "
                    role_ids.append(member.roles[i].id)
            embed.add_field(name="付与されていたロール", value=f"{role_text}")
            await channel.send(embed=embed)
            if member.guild.id not in n_fc.role_keeper:
                n_fc.role_keeper[member.guild.id] = {"rk":0}
                return
            if n_fc.role_keeper[member.guild.id]["rk"] == 1:
                n_fc.role_keeper[member.guild.id][member.id] = role_ids
            save()
            return
        except BaseException as err:
            logging.error(f"ユーザー離脱時の情報表示システムのエラー\n{err}")
            return

def setup(bot):
    bot.add_cog(user_join(bot))