from nextcord.ext import commands
import nextcord
import re
import sys
import json
from cogs.debug import save
from cogs.embed import embed
import asyncio
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

        try:
            channel = self.bot.get_channel(n_fc.welcome_id_list[member.guild.id])
            if member.guild.id not in n_fc.role_keeper:
                n_fc.role_keeper[member.guild.id] = {"rk": 0}
                for i in range(len(member.guild.members)):
                    if member.guild.members[i].id != member.id:
                        n_fc.role_keeper[member.guild.id][member.guild.members[i].id] = [j.id for j in member.guild.members[i].roles if j.name != "@everyone"]

            if member.id not in n_fc.role_keeper[member.guild.id]:
                embed = nextcord.Embed(title="こんにちは！", description=f"名前： `{member.name}`\nID: `{member.id}`", color=0x00ff00)
            else:
                embed = nextcord.Embed(title="あれ、また会った？", description=f"名前： `{member.name}`\nID: `{member.id}`", color=0x00ff00)

            embed.set_thumbnail(url=f"https://cdn.discordapp.com/avatars/{member.id}/{str(member.avatar)}")
            embed.add_field(name="アカウント製作日", value=f"```{member.created_at}```")
            embed.add_field(name="現在のユーザー数", value=f"`{len(member.guild.members)}`人")
            if member.guild.id in n_fc.welcome_id_list:
                members_message = await channel.send(embed=embed)
            else:
                members_message = None

        except BaseException as err:
            logging.error(err)
        
        await asyncio.sleep(2)

        if n_fc.role_keeper[member.guild.id]["rk"] == 1:

            try:
                
                if member.id not in n_fc.role_keeper[member.guild.id]:
                    n_fc.role_keeper[member.guild.id][member.id] = [i.id for i in member.roles if i.name != "@everyone"]
                
                else:
                    role_text = ""
                    for i in range(len(n_fc.role_keeper[member.guild.id][member.id])):
                        role = member.guild.get_role(n_fc.role_keeper[member.guild.id][member.id][i])
                        await member.add_roles(role)
                
                    embed.add_field(name="付与済みロール", value=f"{' '.join([f'<@&{i}>' for i in n_fc.role_keeper[member.guild.id][member.id]])}")
                    await members_message.edit(embed=embed)

            except BaseException as err:
                await members_message.edit(f"ロール付与時に何かしらのエラーが発生しました。\n何度も発生する場合はお問い合わせください。\n`{err}`", embed=embed)
                logging.error(err)

            return



    @commands.Cog.listener()
    async def on_member_remove(self, member):
        user_id = member.id
        try:
            user = await self.bot.fetch_user(user_id)
            if member.guild.id not in n_fc.welcome_id_list:
                return
            channel = self.bot.get_channel(n_fc.welcome_id_list[member.guild.id])
            embed = nextcord.Embed(title="また来てねー！", description=f"名前：`{user.name}`\nID：`{user.id}`", color=0x00ff00)
            embed.set_thumbnail(url=f"https://cdn.discordapp.com/avatars/{user.id}/{str(user.avatar)}")
            embed.add_field(name="現在のユーザー数", value=f"`{len(member.guild.members)}`人")
            role_text = ""
            role_ids = []
            for i in range(len(member.roles)):
                if member.roles[i].name == "@everyone":
                    role_text = role_text + f" {member.roles[i].name} "
                else:
                    role_text = role_text + f" <@&{member.roles[i].id}> "
                    role_ids.append(member.roles[i].id)
            embed.add_field(name="付与されていたロール", value=f"{role_text}")
            removed_message = await channel.send(embed=embed)
            if member.guild.id not in n_fc.role_keeper:
                n_fc.role_keeper[member.guild.id] = {"rk":0}
                return
            if n_fc.role_keeper[member.guild.id]["rk"] == 1:
                n_fc.role_keeper[member.guild.id][member.id] = role_ids
            save()
            return
        except BaseException as err:
            await removed_message.edit(f"おっと...これは大変ですね...\nユーザー離脱時の処理時にエラーが発生しました。\n`{err}`", embed=embed)
            logging.error(f"ユーザー離脱時の情報表示システムのエラー\n{err}")
            return

def setup(bot):
    bot.add_cog(user_join(bot))