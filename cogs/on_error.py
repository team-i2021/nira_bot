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


# エラー時のイベント！
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
                command_list = [i.name for i in list(self.bot.commands)]
                keyword_command = str(event)[9:-14]
                close_command = get_close_matches(
                    word=keyword_command, possibilities=command_list, n=1, cutoff=0)[0]
                close_description = [i.help for i in list(
                    self.bot.commands) if i.name == close_command][0]
                close_oneline = ""
                if not close_description is None:
                    close_oneline = close_description.splitlines()[0]
                else:
                    close_oneline = "(ヘルプがないコマンド)"
                await ctx.reply(embed=nextcord.Embed(title="エラー", description=f"`{self.bot.command_prefix}{keyword_command}`というコマンドは存在しません。\n`n!help`でコマンドを確認してください。\n\nもしかして：`{self.bot.command_prefix}{close_command}`:`{close_oneline}`", color=0xff0000))
            else:
                await ctx.reply(embed=nextcord.Embed(title="エラー", description=f"エラーが発生しました。\n\n・エラー内容```py\n{str(event)}```\n```sh\n{traceback.format_exc()}```\n```py\n{sys.exc_info()}```\n[サポートサーバー](https://discord.gg/awfFpCYTcP)", color=0xff0000))
                logging.error(f"エラーが発生しました。\non_error：{str(event)}")
            return
        except Exception as err:
            await ctx.reply(f"""\
エラー処理中に更にエラーが発生しました。
```{traceback.format_exc()}```
・デバッグ用
`{[keyword_command,close_command,close_description]}`
""")
            logging.error(
                f"エラー処理中のエラー\non_error：{traceback.format_exc()}\nハンドリング中のエラー：{err}")
            return
    
    @commands.Cog.listener()
    async def on_application_command_error(self, interaction: nextcord.Interaction, event: Exception):
        print([type(event), event.args])
        if interaction.response.is_done():
            await interaction.followup.send(embed=nextcord.Embed(title="エラーが発生しました。", description=f"```py\n{str(event)}```\n```sh\n{traceback.format_exc()}```", color=0xff0000))
        else:
            await interaction.response.send_message(embed=nextcord.Embed(title="エラーが発生しました。", description=f"```py\n{str(event)}```\n```sh\n{traceback.format_exc()}```", color=0xff0000), ephemeral=True)
        logging.error(traceback.format_exc())

def setup(bot):
    bot.add_cog(error(bot))
    importlib.reload(nira_commands)
    importlib.reload(eh)
