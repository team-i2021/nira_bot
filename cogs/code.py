from nextcord.ext import commands
import nextcord
import urllib.parse



class code(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def html(self, ctx: commands.Context):
        if len(ctx.message.content.split(" ",1)) == 1:
            await ctx.reply("引数が足りません。\n`n!html [HTMLコード]`")
            return
        html_code = ctx.message.content.split(" ",1)[1]
        embed = nextcord.Embed(title="Dynamic-page", description=f"ページは[こちら](https://nattyan-tv.github.io/dynamic-page/output.html#{urllib.parse.quote(html_code)})", color=0x00ff00)
        embed.set_footer(text="Powered by Dynamic-page\nhttps://github.com/nattyan-tv/dynamic-page")
        await ctx.reply(embed=embed)

def setup(bot):
    bot.add_cog(code(bot))