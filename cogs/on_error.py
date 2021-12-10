from discord.ext import commands
import discord
import re

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
                await ctx.reply(embed=discord.Embed(title="エラー", description=f"不明なエラーが発生しました。\n\n・エラー内容```py\n{str(event)}```\n\n[サポートサーバー](https://discord.gg/awfFpCYTcP)", color=0xff0000))
            return
        except BaseException as err:
            await ctx.reply(f"エラー処理中に更にエラーが発生しました。\n```{err}```")

def setup(bot):
    bot.add_cog(error(bot))