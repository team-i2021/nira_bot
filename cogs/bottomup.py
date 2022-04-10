import asyncio
from nextcord.ext import commands
import nextcord
import subprocess
from subprocess import PIPE
import os
import sys
from nextcord import Interaction, SlashOption, ChannelType

sys.path.append('../')
from util import admin_check, n_fc, eh

# ボトムアップ的な機能


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

async def MessagePin(bot: nextcord.ext.commands.bot.Bot):
    while True:
        try:
            for i in n_fc.pinMessage.keys():
                for j in n_fc.pinMessage[i].keys():
                    CHANNEL = await bot.fetch_channel(j)
                    if CHANNEL.last_message.content == n_fc.pinMessage[i][j] and CHANNEL.last_message.author.id == bot.user.id:
                        continue
                    messages = await CHANNEL.history(limit=10).flatten()
                    for message in messages:
                        if message.content == n_fc.pinMessage[i][j] and message.author.id == bot.user.id:
                            await message.delete()
                    await CHANNEL.send(n_fc.pinMessage[i][j])
            await asyncio.sleep(5)
        except BaseException:
            pass


class bottomup(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="pin", aliases=("Pin","bottomup","ピン留め","ピン"), help="""\
特定のメッセージを一番下に持ってくることで、いつでもみれるようにする、ピン留めの改良版。

`n!pin on [メッセージ内容...(複数行可)]`

他の誰かがメッセージを送った場合、どんどんどんどんその特定ののメッセージを送ると言うような感じの機能です。
Webhookは使いたくない精神なので、ニラBOTが直々に送ってあげます。感謝しなさい。

offにするには、`n!pin off`と送信してください。

前に送ったピンメッセージが削除されずに送信されて、残っている場合は、にらBOTに適切な権限が与えられているか確認してください。
""")
    async def pin(self, ctx: commands.Context):
        args = ctx.message.content.split(" ", 2)
        if args[1] == "on":
            if len(args) != 3:
                await ctx.reply("・エラー\n引数が足りません。\n`n!pin on [メッセージ内容]`または`n!pin off`")
                return
            if ctx.guild.id not in n_fc.pinMessage:
                n_fc.pinMessage[ctx.guild.id] = {ctx.channel.id: args[2]}
            else:
                n_fc.pinMessage[ctx.guild.id][ctx.channel.id] = args[2]
            await ctx.message.add_reaction("\U0001F197")
            await ctx.reply("Ok")
        elif args[1] == "off":
            if ctx.guild.id not in n_fc.pinMessage or ctx.channel.id not in n_fc.pinMessage[ctx.guild.id]:
                await ctx.reply("このチャンネルにはpinメッセージはありません。")
                return
            else:
                messages = await ctx.channel.history(limit=10).flatten()
                search_message = n_fc.pinMessage[ctx.guild.id][ctx.channel.id]
                del n_fc.pinMessage[ctx.guild.id][ctx.channel.id]
                for i in messages:
                    if i.content == search_message:
                        await i.delete()
                await ctx.reply("登録を解除しました。")
                return
        else:
            await ctx.reply("・エラー\n使い方が違います。\n`n!pin on [メッセージ内容]`または`n!pin off`")
            return


def setup(bot):
    bot.add_cog(bottomup(bot))
