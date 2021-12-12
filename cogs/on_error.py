from discord.ext import commands
import discord
import re

#loggingの設定
import logging
class NoTokenLogFilter(logging.Filter):
    def filter(self, record):
        message = record.getMessage()
        return 'token' not in message

logger = logging.getLogger(__name__)
logger.addFilter(NoTokenLogFilter())
formatter = '%(asctime)s$%(filename)s$%(lineno)d$%(funcName)s$%(levelname)s:%(message)s'
logging.basicConfig(format=formatter, filename='/home/nattyantv/nira.log', level=logging.INFO)

#エラー時のイベント！
class error(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, event: Exception):
        try:
            if isinstance(event, commands.CommandOnCooldown):
                rtime = str(event).split(" ")[7]
                await ctx.reply(embed=discord.Embed(title="エラー", description=f"そのコマンドは現在クールタイム中です。\n```残り：{rtime}```", color=0xff0000))
                return
            if re.search('Command \".*\" is not found', str(event)) or (str(event)[:9] == "Command \"" and str(event)[-14:] == "\" is not found"):
                await ctx.reply(embed=discord.Embed(title="エラー", description=f"`n!{str(event)[9:-14]}`というコマンドは存在しません。\n`n!help`でコマンドを確認してください。", color=0xff0000))
            else:
                await ctx.reply(embed=discord.Embed(title="エラー", description=f"エラーが発生しました。\n\n・エラー内容```py\n{str(event)}```\n\n[サポートサーバー](https://discord.gg/awfFpCYTcP)", color=0xff0000))
                logging.error(f"エラーが発生しました。\non_error：{str(event)}")
            return
        except BaseException as err:
            await ctx.reply(f"エラー処理中に更にエラーが発生しました。\n```{err}```")
            logging.error(f"エラー処理中のエラー\non_error：{str(event)}\nハンドリング中のエラー：{err}")
            return

def setup(bot):
    bot.add_cog(error(bot))