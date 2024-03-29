import nextcord
from nextcord.ext import commands
from util.nira import NIRA

# 変数読み込むまで....


class not_ready(commands.Cog):
    def __init__(self, bot: NIRA):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message):
        return
        if message.content.startswith(f"{self.bot.command_prefix}"):
            await message.reply("現在起動準備中です。")


def setup(bot):
    bot.add_cog(not_ready(bot))
