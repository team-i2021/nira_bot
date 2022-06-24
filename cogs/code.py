import urllib.parse

import nextcord
from nextcord import Interaction
from nextcord.ext import commands

from util.n_fc import GUILD_IDS


class CodeInsert(nextcord.ui.Modal):
    def __init__(self):
        super().__init__(
            "HTML Code",
            timeout=None,
        )

        self.code = nextcord.ui.TextInput(
            label="HTMLコード",
            style=nextcord.TextInputStyle.paragraph,
            placeholder="<h1>Hello, world!</h1><h5>See you, world...!</h5>",
            required=True,
        )
        self.add_item(self.code)

    async def callback(self, interaction: nextcord.Interaction) -> None:
        embed = nextcord.Embed(title="Dynamic-page", description=f"ページは[こちら](https://nattyan-tv.github.io/dynamic-page/output.html#{urllib.parse.quote(self.code.value)})", color=0x00ff00)
        embed.set_footer(text="Powered by Dynamic-page\nhttps://github.com/nattyan-tv/dynamic-page")
        await interaction.send(embed=embed)


class Code(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @nextcord.slash_command(name="html", description="HTMLを入力してページを返します。", guild_ids=GUILD_IDS)
    async def html_slash(self, interaction: Interaction):
        modal = CodeInsert()
        await interaction.response.send_modal(modal=modal)

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
    bot.add_cog(Code(bot))
