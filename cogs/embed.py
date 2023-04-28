import re
from io import StringIO

import nextcord
from nextcord import Interaction
from nextcord.ext import commands

from util import n_fc, eh
from util.nira import NIRA

# embedを送信する機能


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
            max_length=256,
            required=True,
        )
        self.add_item(self.embed_title)

        self.embed_color = nextcord.ui.TextInput(
            label="色",
            style=nextcord.TextInputStyle.short,
            placeholder="#00ff00",
            min_length=7,
            max_length=7,
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
        ephemeral = False
        files = []

        if re.fullmatch(r"#[0-9a-f]{6}", self.embed_color.value, re.I) is not None:
            embed = nextcord.Embed(
                title=self.embed_title.value,
                description=self.embed_description.value,
                color=int(self.embed_color.value[1:], 16),
            )

        else:
            ephemeral = True
            embed = nextcord.Embed(
                title="Error",
                description="カラーコードが不正です。[こちら](https://bratcreator.work/color-code/)をご覧ください。\n入力した内容は添付ファイルから確認できます。",
                color=0xff0000,
            )
            embed.add_field(
                name="iPhoneをご利用の方",
                value="ファイルをタップした後、右下にあるコンパスアイコンのボタンを押すとブラウザでファイルを開くことができます。\nSafariの場合はさらに[表示]を押してください。",
                inline=False
            )
            text = StringIO(f"""\
・タイトル
{self.embed_title.value}

・色
{self.embed_color.value}

・本文
{self.embed_description.value}
""")
            files.append(nextcord.File(
                text, filename="embed.txt", description="入力した内容"))

        await interaction.send(embed=embed, files=files, ephemeral=ephemeral)


class SendEmbed(commands.Cog):
    def __init__(self, bot: NIRA, **kwargs):
        self.bot = bot
        self.mscommands = self.embed_message_command

    # @nextcord.message_command(name="Embedコンテンツの取得", guild_ids=n_fc.GUILD_IDS)
    async def embed_message_command(self, interaction: Interaction, message: nextcord.Message):
        await interaction.response.defer(ephemeral=True)
        if len(message.embeds) == 0:
            await interaction.followup.send(embed=nextcord.Embed(title="エラー", description="指定されたメッセージにはEmbedがついていません。", color=0xff0000))
            return
        content = ""
        for i in message.embeds:
            content += i.description + "\n\n"
            for j in i.fields:
                content += j.value + "\n"
            content += "\n"
        await interaction.followup.send(content)

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
        if ctx.message.content == f"{self.bot.command_prefix}embed":
            embed = nextcord.Embed(
                title="Error", description=f"構文が間違っています。\n```{self.bot.command_prefix}embed [color(000000～ffffff)] [title]\n[description]```", color=0xff0000)
            await ctx.reply(embed=embed)
            return
        try:
            mes_ch = ctx.message.content.splitlines()
            emb_clr = int(
                "".join(re.findall(r'[0-9a-f]', str(mes_ch[0].split(" ", 3)[1]))), 16)
            emb_title = str(mes_ch[0].split(" ", 3)[2])
            emb_desc = "\n".join(mes_ch[1:])
            embed = nextcord.Embed(
                title=emb_title, description=emb_desc, color=emb_clr)
            await ctx.send(embed=embed)
            return
        except Exception as err:
            await ctx.reply(embed=eh.eh(self.bot.client, err))
            return


def setup(bot, **kwargs):
    bot.add_cog(SendEmbed(bot, **kwargs))
