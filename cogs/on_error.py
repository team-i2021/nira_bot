import importlib
import logging
import os
import re
import sys
import traceback
from difflib import get_close_matches

import nextcord
from nextcord.ext import commands

import nira_commands
from util import eh
from util.nira import NIRA


# エラー時のイベント！
class error(commands.Cog):
    def __init__(self, bot: NIRA, **kwargs):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, event: Exception):
        try:
            error = getattr(event, "original", event)
            if isinstance(error, commands.CommandOnCooldown):
                rtime = str(error).split(" ")[7]
                await ctx.reply(embed=nextcord.Embed(title="429 - Too Many Requests", description=f"そのコマンドは現在クールタイム中です。\n```残り：{rtime}```", color=0xff0000))
            elif isinstance(error, commands.CommandNotFound):
                command_list = [i.name for i in list(self.bot.commands)]
                keyword_command = re.findall(r"\".+\"", str(error))[0][1:-1]
                close_command = get_close_matches(
                    word=keyword_command, possibilities=command_list, n=1, cutoff=0)[0]
                close_description = [i.help for i in list(
                    self.bot.commands) if i.name == close_command][0]
                close_oneline = ""
                if close_description is not None:
                    close_oneline = close_description.splitlines()[0]
                else:
                    close_oneline = "(ヘルプがないコマンド)"
                await ctx.reply(embed=nextcord.Embed(title="404 - Not Found", description=f"`{self.bot.command_prefix}{keyword_command}`というコマンドは存在しません。\n`{self.bot.command_prefix}help`でコマンドを確認してください。\n\nもしかして：`{self.bot.command_prefix}{close_command}`:`{close_oneline}`", color=0xff0000))
            elif isinstance(error, NIRA.Forbidden):
                await ctx.reply(embed=nextcord.Embed(title="403 - Forbidden", description="このコマンドを実行するのに必要な権限がありません。", color=0xff0000))
            elif isinstance(error, NIRA.ForbiddenExpand):
                await ctx.reply(embed=nextcord.Embed(title="403 - Forbidden", description="このコマンドは管理者のみが使用できます。", color=0xff0000))
            else:
                ev = str(error).replace(self.bot.client.url, "[URL]")
                tb = str(traceback.format_exc()).replace(self.bot.client.url, "[URL]")
                await ctx.reply(embed=nextcord.Embed(title="エラー", description=f"エラーが発生しました。\n\n・エラー内容```py\n{ev}```\n```sh\n{tb}```\n```py\n{sys.exc_info()}```\n[サポートサーバー](https://discord.gg/awfFpCYTcP)", color=0xff0000))
                logging.error(vars(ctx), exc_info=True)
            return
        except Exception as err:
            await ctx.reply(f"""\
エラー処理中に更にエラーが発生しました。
```{tb}```
・デバッグ用
`{[keyword_command,close_command,close_description]}`
""")
            logging.error(
                f"エラー処理中のエラー\non_error：{traceback.format_exc()}\nハンドリング中のエラー：{err}", exc_info=True)
            return

    @commands.Cog.listener()
    async def on_application_command_error(self, interaction: nextcord.Interaction, event: Exception):
        error = getattr(event, "original", event)
        ev = str(event).replace(self.bot.client.url, "[URL]")
        tb = str(traceback.format_exc()).replace(self.bot.client.url, "[URL]")
        await interaction.send(embed=nextcord.Embed(title="エラーが発生しました。", description=f"```py\n{ev}```\n```sh\n{tb}```", color=0xff0000), ephemeral=True)
        logging.error(vars(interaction), exc_info=True)

def setup(bot, **kwargs):
    bot.add_cog(error(bot, **kwargs))
    importlib.reload(nira_commands)
    importlib.reload(eh)
