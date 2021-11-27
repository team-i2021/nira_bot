from discord.ext import commands
import discord

class ping(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx: commands.Context):
        embed = discord.Embed(title="Ping", description=f"現在のPing値は`{round(self.bot.latency * 1000)}`msです。", color=0x00ff00)
        await ctx.reply(embed=embed)
        return

def setup(bot):
    bot.add_cog(ping(bot))