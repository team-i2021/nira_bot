from nextcord.ext import commands
from nextcord import Interaction, SlashOption
import nextcord
import re
import pickle

import sys,os

from cogs.debug import save
from util import admin_check, n_fc, eh, slash_tool

SET, DEL, STATUS = (0, 1, 2)

#ユーザー情報表示系

home_dir = sys.path[0]

class user(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @nextcord.slash_command(
            name="user",
            description="ユーザー情報表示",
            guild_ids=n_fc.GUILD_IDS
        )
    async def user_slash(
            self,
            interaction: Interaction,
            user: nextcord.User = SlashOption(
                name = "user",
                description = "情報を表示するユーザー",
                required=False
            )
        ):
        if user == None:
            user = interaction.user
        embed = nextcord.Embed(title="User Info", description=f"名前：`{user.name}`\nID：`{user.id}`", color=0x00ff00)
        embed.set_thumbnail(url=user.avatar.url)
        embed.add_field(name="アカウント製作日", value=f"```{user.created_at}```")
        await interaction.response.send_message(embed=embed)
        return
    
    @commands.command(name="d", help="""\
    ユーザーの情報を表示します。
    引数を指定せずに`n!d`とだけ指定するとあなた自身の情報を表示します。
    `n!d [ユーザーID]`という風に指定すると、そのユーザーの情報を表示することが出来ます。
    ユーザーIDの指定方法は...多分調べれば出てきます。
    **メンションでも指定できますが、いざこざとかにつながるかもしれないのでしないほうが得策です。**""")
    async def d(self, ctx: commands.Context):
        if ctx.message.content == "n!d":
            user = await self.bot.fetch_user(ctx.message.author.id)
            embed = nextcord.Embed(title="User Info", description=f"名前：`{user.name}`\nID：`{user.id}`", color=0x00ff00)
            embed.set_thumbnail(url=user.avatar.url)
            embed.add_field(name="アカウント製作日", value=f"```{user.created_at}```")
            await ctx.message.reply(embed=embed)
            return
        else:
            user_id = int("".join(re.findall(r'[0-9]', ctx.message.content[4:])))
            try:
                user = await self.bot.fetch_user(user_id)
                embed = nextcord.Embed(title="User Info", description=f"名前：`{user.name}`\nID：`{user.id}`", color=0x00ff00)
                embed.set_thumbnail(url=user.avatar.url)
                embed.add_field(name="アカウント製作日", value=f"```{user.created_at}```")
                await ctx.message.reply(embed=embed)
                return
            except BaseException:
                await ctx.message.reply(embed=nextcord.Embed(title="Error", description="ユーザーが存在しないか、データが取得できませんでした。", color=0xff0000))
                return
    
    @nextcord.slash_command(name="rk", description="ロールキーパー機能の設定")
    async def rk_slash(self, interaction: Interaction):
        pass

    @commands.command(name="rk", help="""\
ロールキーパー機能です。
大前提、**ちゃんと機能するとは思わないでください。**
`n!rk [on/off]`でロールキーパー機能の設定が可能です。ただ、ロールキーパー機能を有効にするには`n!ui`の、ユーザー情報表示を有効にしないと有効になりません。""")
    async def rk(self, ctx: commands.Context):
        if admin_check.admin_check(ctx.message.guild, ctx.message.author) or ctx.message.author.id in n_fc.py_admin:
            if ctx.message.content == "n!rk":
                embed = nextcord.Embed(title="ロールキーパー", description="`n!rk [on/off]`", color=0x00ff00)
                if ctx.guild.id not in n_fc.role_keeper:
                    n_fc.role_keeper[ctx.guild.id] = {"rk":0}
                    save()
                if n_fc.role_keeper[ctx.guild.id]["rk"] == 0:
                    role_bool = "無効"
                else:
                    role_bool = "有効"
                embed.add_field(name="ロールキーパーの状態", value=f"ロールキーパーは現在{role_bool}です")
                await ctx.reply(embed=embed)
                return
            if ctx.message.content[5:] in n_fc.on_ali:
                # ロールキーパーオンにしやがれ
                if ctx.guild.id not in n_fc.role_keeper:
                    n_fc.role_keeper[ctx.guild.id] = {"rk":1}
                else:
                    n_fc.role_keeper[ctx.guild.id]["rk"] = 1
            elif ctx.message.content[5:] in n_fc.off_ali:
                # ロールキーパーオフにしやがれ
                if ctx.guild.id not in n_fc.role_keeper:
                    n_fc.role_keeper[ctx.guild.id] = {"rk":0}
                else:
                    n_fc.role_keeper[ctx.guild.id]["rk"] = 0
            else:
                await ctx.reply("値が不正です。\n「on」とか「off」とか...")
                return
            save()
            await ctx.reply("ロールキーパーの設定を更新しました。")
            return
        else:
            await ctx.reply("権限がありません。")


    async def ui_config(bot: commands.Bot, interaction: Interaction or commands.Context, type: int, guild_id: int, channel: nextcord.channel):
        if type == SET:
            try:
                n_fc.welcome_id_list[guild_id] = channel.id
                save()
                CHANNEL = await bot.fetch_channel(n_fc.welcome_id_list[guild_id])
                await CHANNEL.send("このチャンネルが、ユーザー情報表示チャンネルとして指定されました。")
                return slash_tool.messages.mreply(interaction, embed=nextcord.Embed(title="ユーザー情報表示設定",description=f"<#{channel.id}>に指定されました。", color=0x00ff00),ephemeral=True)
            except BaseException as err:
                return slash_tool.messages.mreply(interaction, embed=nextcord.Embed(title="ユーザー情報表示設定",description=f"エラーが発生しました。\n```\n{err}```", color=0xff000),ephemeral=True)
        elif type == DEL:
            try:
                if guild_id not in n_fc.welcome_id_list:
                    return slash_tool.messages.mreply(interaction, embed=nextcord.Embed(title="ユーザー情報表示設定",description=f"このサーバーには登録されていません。", color=0xff0000), ephemeral=True)
                del n_fc.welcome_id_list[guild_id]
                return slash_tool.messages.mreply(interaction, embed=nextcord.Embed(title="ユーザー情報表示設定",description=f"設定を削除しました。", color=0x00ff00),ephemeral=True)
            except BaseException as err:
                return slash_tool.messages.mreply(interaction, embed=nextcord.Embed(title="ユーザー情報表示設定",description=f"エラーが発生しました。\n```\n{err}```", color=0xff000),ephemeral=True)
        elif type == STATUS:
            if guild_id not in n_fc.welcome_id_list:
                return slash_tool.messages.mreply(interaction, embed=nextcord.Embed(title="ユーザー情報表示設定",description=f"サーバーで設定は`無効`です", color=0x00ff00),ephemeral=True)
            else:
                return slash_tool.messages.mreply(interaction, embed=nextcord.Embed(title="ユーザー情報表示設定",description=f"サーバーで設定は`有効`です\n設定チャンネル: <#{n_fc.welcome_id_list[guild_id]}>", color=0x00ff00),ephemeral=True)

    @nextcord.slash_command(name="ui", description="サーバー加入/離脱した場合にそのユーザーの情報を表示します")
    async def ui_slash(self, interaction):
        pass

    @ui_slash.subcommand(name="set", description="ユーザー表示チャンネルをセットします")
    async def set_slash(
            self,
            interaction: Interaction,
            channel: nextcord.abc.GuildChannel = SlashOption(
                name="channel",
                description="メッセージを送信するチャンネルです",
                required=True
            )
        ):
        if admin_check(interaction.guild, interaction.user):
            await self.ui_config(self.bot, interaction, SET, interaction.guild.id, channel)
        else:
            await interaction.response.send_message("管理者権限がありません。", ephemeral=True)
        return

    @ui_slash.subcommand(name="del", description="ユーザー表示チャンネル設定を削除します")
    async def del_slash(
            self,
            interaction: Interaction
        ):
        if admin_check(interaction.guild, interaction.user):
            await self.ui_config(self.bot, interaction, DEL, interaction.guild.id, None)
        else:
            await interaction.response.send_message("管理者権限がありません。", ephemeral=True)
        return

    @ui_slash.subcommand(name="status", description="ユーザー表示チャンネル設定を確認します")
    async def status_slash(
            self,
            interaction: Interaction
        ):
        if admin_check(interaction.guild, interaction.user):
            await self.ui_config(self.bot, interaction, STATUS, interaction.guild.id, None)
        else:
            await interaction.response.send_message("管理者権限がありません。", ephemeral=True)
        return

    @commands.command(name="ui", help="""\
    誰かがDiscordサーバーに加入/離脱した際に、指定したチャンネルにそのユーザーの情報を表示します。
    それだけです。""")
    async def ui(self, ctx: commands.Context):
        if admin_check.admin_check(ctx.message.guild, ctx.message.author) or ctx.message.author.id in n_fc.py_admin:
            mes_arg = ctx.message.content.split(" ")
            if len(mes_arg) == 1:
                await self.ui_config(self.bot, ctx, STATUS, ctx.guild.id, None)
                return
            elif mes_arg[1] == "set":
                set_id = int("".join(re.findall(r'[0-9]', mes_arg[2])))
                channel = await self.bot.fetch_channel(set_id)
                await self.ui_config(self.bot, ctx, SET, ctx.guild.id, channel)
                return
            elif  mes_arg[1] == "del":
                await self.ui_config(self.bot, ctx, DEL, ctx.guild.id, None)
                return
            else:
                await self.ui_config(self.bot, ctx, STATUS, ctx.guild.id, None)

        else:
            await ctx.message.reply(embed=nextcord.Embed(title="Error", description=f"管理者権限がありません。", color=0xff0000))
            return

def setup(bot):
    bot.add_cog(user(bot))
