import asyncio
from nextcord.ext import commands
import nextcord
import subprocess
from subprocess import PIPE
import os
import sys
from nextcord import Interaction, SlashOption, ChannelType
from cogs.debug import save

sys.path.append('../')
from util import admin_check, n_fc, eh

# Autorole

#loggingの設定
import logging

class NoTokenLogFilter(logging.Filter):
    def filter(self, record):
        message = record.getMessage()
        return 'token' not in message

logger = logging.getLogger(__name__)
logger.addFilter(NoTokenLogFilter())
formatter = '%(asctime)s$%(filename)s$%(lineno)d$%(funcName)s$%(levelname)s:%(message)s'
logging.basicConfig(format=formatter, filename=f'/home/nattyantv/nira_bot_rewrite/nira.log', level=logging.INFO)

class autorole(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="autorole", aliases=("自動ロール","オートロール"), help="""\
    ユーザーが加入したときに、指定したロールを自動的に付与することが出来ます。
    書き方: `n!autorole [ロール名またはロールID]`

    ・例
    ```
    n!autorole にら民
    ```


    """)
    async def autorole(self, ctx: commands.Context):
        if not admin_check.admin_check(ctx.guild, ctx.author):
            await ctx.reply("・Autoroleコマンド\nエラー：権限がありません。")
            return
        args = ctx.message.content.split(" ", 2)
        if len(args) != 2:
            await ctx.reply(f"・Autoroleコマンド\nエラー：構文が間違っています。\n書き方：`n!autorole [ロール名またはロールID]`")
            return
        role_id = None
        try:
            role_id = int(args[1])
        except ValueError:
            roles = ctx.guild.roles
            for i in range(len(roles)):
                if roles[i].name == args[1]:
                    role_id = roles[i].id
                    break
            if role_id == None:
                await ctx.reply("・Autoroleコマンド\nエラー：指定したロールが存在しません。")
                return
        if role_id == None:
            await ctx.reply("・Autoroleコマンド\nエラー：指定したロールが存在しません。")
            return
        n_fc.autorole[ctx.guild.id] = role_id
        await ctx.reply(embed=nextcord.Embed(title="・Autoroleコマンド", description=f"設定完了：{ctx.guild.get_role(role_id).mention}を自動的に付与します。"))
        save()
        return
    
    @commands.Cog.listener()
    async def on_member_join(self, member: nextcord.Member):
        if member.guild.id in n_fc.autorole:
            role = member.guild.get_role(n_fc.autorole[member.guild.id])
            await member.add_role(role)
            return
        return

def setup(bot):
    bot.add_cog(autorole(bot))