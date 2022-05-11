from nextcord.ext import commands
import nextcord
import re
from nextcord import Interaction

import sys
sys.path.append('../')
from util import admin_check, n_fc, eh

#embedを送信する機能


## 作ったはいいものの動かないから困ってます()
## The above exception was the direct cause of the following exception:
## nextcord.errors.ApplicationInvokeError: Command raised an exception: TypeError: Object of type TextInput is not JSON serializable
class EmbedMaker(nextcord.ui.Modal):
    def __init__(self):
        super().__init__(
            "EmbedMaker",
            timeout=None,
        )

        self.embed_title = nextcord.ui.TextInput(
            label="タイトル",
            style=nextcord.TextInputStyle.short,
            placeholder="ご報告！",
            required=True,
        )
        self.add_item(self.embed_title)

        self.embed_color = nextcord.ui.TextInput(
            label="色",
            style=nextcord.TextInputStyle.short,
            placeholder="#00ff00",
            required=True,
        )
        self.add_item(self.embed_color)

        self.embed_description = nextcord.ui.TextInput(
            label="本文",
            style=nextcord.TextInputStyle.paragraph,
            placeholder="にらBOTを導入しました！いえい！",
            required=True,
        )
        self.add_item(self.embed_description)

    async def callback(self, interaction: nextcord.Interaction) -> None:
        embed = nextcord.Embed(
            title=self.embed_title.value,
            description=self.embed_description.value,
            color=int("".join(re.findall(r"[0-9]|[a-f]",self.embed_color.value).group(), 16)),
        )
        await interaction.send(embed=embed)


class SendEmbed(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @nextcord.slash_command(name="embed", description="Embedを作成して送信します。", guild_ids=n_fc.GUILD_IDS)
    async def embed_slash(self, interaction: Interaction):
        modal = EmbedMaker()
        await interaction.response.send_modal(modal=modal)

    
    @commands.command(name="embed", help="""\
あなたの代わりに**にらBOT**がEmbedを送信します。
```n!embed [color] [title]
[本文]```
というような構成で送ってください。
colorは16進数のRGBカラーコード([#]は不要)です。
カラーコードについては[こちら](https://bratcreator.work/color-code/)を参考にしてください。
カラーコードが送信されないとわけわからん色になる場合があります。

引数1:color(int...?)
RGBのカラーコード。Embedの色になります。

引数2:title(str)
Embedのタイトルになるところです。

引数3:本文(str)
Embedの本文です。
""")
    async def embed(self, ctx: commands.Context):
        if ctx.message.content == "n!embed":
            embed = nextcord.Embed(title="Error", description="構文が間違っています。\n```n!embed [color(000000～ffffff)] [title]\n[description]```", color=0xff0000)
            await ctx.message.reply(embed=embed)
            return
        try:
            mes_ch = ctx.message.content.splitlines()
            emb_clr = int("".join(re.findall(r'[0-9]|[a-f]', str(mes_ch[0].split(" ", 3)[1]))), 16)
            emb_title = str(mes_ch[0].split(" ", 3)[2])
            emb_desc = "\n".join(mes_ch[1:])
            embed = nextcord.Embed(title=emb_title, description=emb_desc, color=emb_clr)
            await ctx.send(embed=embed)
            return
        except BaseException as err:
            await ctx.message.reply(embed=eh.eh(err))
            return


def setup(bot):
    bot.add_cog(SendEmbed(bot))
