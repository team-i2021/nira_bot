from nextcord.ext import commands
import nextcord
import re
import sys
import os
import difflib
import nira_commands
import importlib

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

#エラー時のイベント！
class error(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, event: Exception):
        try:
            if isinstance(event, commands.CommandOnCooldown):
                rtime = str(event).split(" ")[7]
                await ctx.reply(embed=nextcord.Embed(title="エラー", description=f"そのコマンドは現在クールタイム中です。\n```残り：{rtime}```", color=0xff0000))
                return
            if re.search('Command \".*\" is not found', str(event)) or (str(event)[:9] == "Command \"" and str(event)[-14:] == "\" is not found"):
                # 類似度を計算、0.0~1.0 で結果が返る
                ruizi_max = 0.0
                for i in range(len(nira_commands.commands_list)):
                    ruizi = difflib.SequenceMatcher(None, str(event)[9:-14], nira_commands.commands_list[i]).ratio()
                    if ruizi > ruizi_max:
                        ruizi_cm = i
                        ruizi_max = ruizi
                await ctx.reply(embed=nextcord.Embed(title="エラー", description=f"`n!{str(event)[9:-14]}`というコマンドは存在しません。\n`n!help`でコマンドを確認してください。\n\nもしかして：`n!{nira_commands.commands_list[ruizi_cm]}`:`{nira_commands.commands_desc[ruizi_cm]}`", color=0xff0000))
            else:
                await ctx.reply(embed=nextcord.Embed(title="エラー", description=f"エラーが発生しました。\n\n・エラー内容```py\n{str(event)}```\n```sh\n{sys.exc_info()}```\n[サポートサーバー](https://discord.gg/awfFpCYTcP)", color=0xff0000))
                logging.error(f"エラーが発生しました。\non_error：{str(event)}")
            return
        except BaseException as err:
            await ctx.reply(f"エラー処理中に更にエラーが発生しました。\n```{err}```")
            logging.error(f"エラー処理中のエラー\non_error：{str(event)}\nハンドリング中のエラー：{err}")
            return

def setup(bot):
    bot.add_cog(error(bot))
    importlib.reload(nira_commands)