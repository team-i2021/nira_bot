import asyncio
import json
import os
import sys

import nextcord
from nextcord import Interaction, SlashOption
from nextcord.ext import commands

from util import n_fc


CaptchaData = {}


# reading

# web captcha

class CaptchaView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @nextcord.ui.button(label="認証をする", style=nextcord.ButtonStyle.green)
    async def captcha(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await interaction.response.send_message("Web認証を行うには下のボタンを押してください。", ephemeral=True, view=CaptchaView(interaction.guild.id, interaction.user.id))
        return


class CaptchaButton(nextcord.ui.View):
    def __init__(self, guild_id: int, user_id: int):
        super().__init__(timeout=None)
        url = f"https://nira.f5.si/captcha.html?guild_id={guild_id}&user_id={user_id}"
        self.add_item(nextcord.ui.Button(label="認証", url=url,
                      style=nextcord.ButtonStyle.green))


class CaptchaSetting(nextcord.ui.View):
    def __init__(self, author: int, role_id: int):
        super().__init__(timeout=None)
        self.author = author
        self.role_id = role_id

    @nextcord.ui.button(label="設定を変更する", style=nextcord.ButtonStyle.danger)
    async def callback(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await interaction.response.defer()
        if interaction.user.id == self.author:
            CaptchaData[interaction.guild.id] = self.role_id
            #database.writeValue(DBS, DATABASE_KEY, CaptchaData)
            await interaction.followup.send(embed=nextcord.Embed(title="Web認証", description=f"認証を設定しました。\n認証ページで認証をすると <#&{CaptchaData[interaction.guild.id]}> が付与されます。", color=0x00ff00), ephemeral=True)
            await asyncio.sleep(1)
            await interaction.channel.send(embed=nextcord.Embed(title="Web認証", description="認証を行うには下のボタンを押してください。", view=CaptchaView()))
        else:
            await interaction.followup.send(embed=nextcord.Embed(title="Web認証 - エラー", description="コマンド送信者と同じ人がボタンを押すことができます。", color=0xff0000), ephemeral=True)
        return


class Captcha(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @nextcord.slash_command(name="captcha", description="Web認証を設定します。")
    async def captcha_slash(
        self,
        interaction: Interaction,
        role: nextcord.Role = SlashOption(
            name="role",
            description="認証成功時に付与するロールです。",
            required=True
        )
    ):
        await interaction.response.defer()
        if interaction.guild.id in CaptchaData:
            await interaction.followup.send(embed=nextcord.Embed(title="このサーバーには既に認証が設定されています。", description=f"このサーバーには <#&{CaptchaData[interaction.guild.id]}> に認証が設定されています。\n新しく認証を作成すると、前の認証は <@&{role.id}> に上書きされます。\n設定してもよろしいですか？\nよろしければ下のボタンを押してください。", color=0x00ff00), view=CaptchaSetting(interaction.author.id, role.id), ephemeral=True)
            return
        else:
            CaptchaData[interaction.guild.id] = self.role_id
            #database.writeValue(DBS, DATABASE_KEY, CaptchaData)
            await interaction.followup.send(embed=nextcord.Embed(title="Web認証", description=f"認証を設定しました。\n認証ページで認証をすると <#&{CaptchaData[interaction.guild.id]}> が付与されます。", color=0x00ff00), ephemeral=True)
            await asyncio.sleep(1)
            await interaction.channel.send(embed=nextcord.Embed(title="Web認証", description="認証を行うには下のボタンを押してください。", view=CaptchaView()))
        return

    @commands.command(name="captcha", help="""\
Web認証を設定します

荒らし対策としてWeb認証を設定します。
認証に成功するとロールが付与されるというようなものです。
reCapthaなんで、強いとは思うんですけど、それよりバグが心配で心配であーたまらない！

なお、各サーバーにつき1つしかWeb認証はつけられません。

・使い方
`n!captcha [付与したいロールIDまたは名前]`
`/captcha role:[付与したいロール]`

認証を促すメッセージが、チャンネルに送信されます。
ボタンを押すことで認証ページに飛んで、Captchaが成功すると指定したロールが付与されます。
""")
    async def captcha(self, ctx: commands.Context):
        args = ctx.message.content.split(" ", 1)

        if len(args) == 1:
            await ctx.reply(embed=nextcord.Embed(title="Web認証", description=f"Web認証を行うボタンを送信します。\n`{self.bot.command_prefix}captcha [付与したいロールID又は名前]`", color=0x00ff00))
            return

        role_id = None

        try:
            role_id = int(args[1])
        except ValueError:
            roles = ctx.guild.roles
            for j in range(len(roles)):
                if roles[j].name == args[1]:
                    role_id = roles[j].id
                    break

        if role_id == None:
            await ctx.reply(embed=nextcord.Embed(title="Web認証 - エラー", description=f"指定したロール`{args[1]}`が見つかりませんでした。\n`{self.bot.command_prefix}captcha [付与したいロールID又は名前]`", color=0xff0000))
            return

        if ctx.guild.id in CaptchaData:

            def check(m):
                return (m.content == 'y' or m.content == 'n') and m.author == ctx.author and m.channel == ctx.channel

            action = await ctx.reply(embed=nextcord.Embed(title="このサーバーには既に認証が設定されています。", description=f"このサーバーには <#&{CaptchaData[ctx.guild.id]}> に認証が設定されています。\n新しく認証を作成すると、前の認証は <@&{role_id}> に上書きされます。\n設定してもよろしいですか？\n10秒以内に`y`/`n`で答えてください。\n\n`y`: 設定する\n`n`: 設定しない", color=0x00ff00))

            try:
                msg = await self.bot.wait_for('message', check=check, timeout=10)
            except asyncio.TimeoutError:
                await action.edit(content="時間切れです。\n再度やり直してください。", embed=None)
                return

            if msg.content == "n":
                await action.edit(content="設定をキャンセルしました。", embed=None)
                return
            elif msg.content == "y":
                CaptchaData[ctx.guild.id] = role_id
                await action.delete()
                #database.writeValue(database, DATABASE_KEY, CaptchaData)
                await ctx.reply(embed=nextcord.Embed(title="Web認証", description=f"認証を設定しました。\n認証ページで認証をすると <#&{CaptchaData[ctx.guild.id]}> が付与されます。", color=0x00ff00))
                await asyncio.sleep(1)
                await ctx.channel.send(embed=nextcord.Embed(title="Web認証", description="認証を行うには下のボタンを押してください。", view=CaptchaView()))
                return

        else:
            CaptchaData[ctx.guild.id] = role_id
            await action.delete()
            #database.writeValue(database, DATABASE_KEY, CaptchaData)
            await ctx.reply(embed=nextcord.Embed(title="Web認証", description=f"認証を設定しました。\n認証ページで認証をすると <#&{CaptchaData[ctx.guild.id]}> が付与されます。", color=0x00ff00))
            await asyncio.sleep(1)
            await ctx.channel.send(embed=nextcord.Embed(title="Web認証", description="認証を行うには下のボタンを押してください。", view=CaptchaView()))
            return

        return


def setup(bot):
    #readDatabase()
    bot.add_cog(Captcha(bot))


def teardown(bot):
    #database.writeValue(DBS, DATABASE_KEY, CaptchaData)
    return
