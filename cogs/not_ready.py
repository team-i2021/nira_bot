from discord.ext import commands
import discord

# 変数読み込むまで....

class not_ready(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_message(self, message:discord.Message):
        if message.content[:2] == "n!":
            await message.reply("現在起動準備中です。")

def setup(bot):
    bot.add_cog(not_ready(bot))

