import nextcord
from nextcord.ext import commands

# 変数読み込むまで....


class not_ready(commands.Cog):
    def __init__(self, bot: commands.Bot, **kwargs):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message):
        return
        if message.content.startswith(f"{self.bot.command_prefix}"):
            await message.reply("現在起動準備中です。")


def setup(bot, **kwargs):
    bot.add_cog(not_ready(bot, **kwargs))
