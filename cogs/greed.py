from discord.ext import commands

class greed(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def hello(self, ctx: commands.Context):
        await ctx.reply("helllo")

def setup(bot):
    bot.add_cog(greed(bot))