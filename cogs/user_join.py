from discord.ext import commands
import discord

import sys
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
            await channel.send(embed=embed)
            return
        except BaseException as err:
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
            for i in range(len(member.roles)):
                if member.roles[i].name == "@everyone":
                    role_text = role_text + f" {member.roles[i].name} "
                else:
                    role_text = role_text + f" <@&{member.roles[i].id}> "
            embed.add_field(name="付与されていたロール", value=f"{role_text}")
            await channel.send(embed=embed)
            return
        except BaseException as err:
            logging.error(f"ユーザー離脱時の情報表示システムのエラー\n{err}")
            return

def setup(bot):
    bot.add_cog(user_join(bot))