import asyncio
import os
import pickle
import re
import sys

import HTTP_db
import nextcord
from nextcord import Interaction, SlashOption
from nextcord.ext import commands

from cogs.debug import save
from util import admin_check, eh, slash_tool, database, n_fc

SET, DEL, STATUS = (0, 1, 2)

# ユーザー情報表示系


class RoleKeeper:
    name = "role_kepper"
    value = {}
    default = {}
    value_type = database.CHANNEL_VALUE


class WelcomeInfo:
    name = "welcome_info"
    value = {}
    default = {}
    value_type = database.GUILD_VALUE


class user(commands.Cog):
    def __init__(self, bot: commands.Bot, **kwargs):
        self.bot = bot
        self.client = kwargs["client"]

    def UserInfoEmbed(self, member: nextcord.Member or nextcord.User):
        if member.bot:
            embed = nextcord.Embed(
                title="User Info",
                description=f"名前：`{member.name}` __[BOT]__\nID：`{member.id}`",
                color=0x00ff00
            )
        else:
            embed = nextcord.Embed(
                title="User Info",
                description=f"名前：`{member.name}`\nID：`{member.id}`",
                color=0x00ff00
            )
        if member.banner is not None:
            embed.set_image(url=member.banner.url)
        if member.avatar is not None:
            embed.set_thumbnail(url=member.avatar.url)
        embed.add_field(
            name="アカウント製作日",
            value=f"```{member.created_at}```",
            inline=False
        )
        if type(member) is nextcord.Member:
            embed.add_field(
                name="サーバー参加日",
                value=f"```{member.joined_at}```",
                inline=False
            )

        return embed

    @nextcord.user_command(name="ユーザー情報表示", guild_ids=n_fc.GUILD_IDS)
    async def member_info(self, interaction: Interaction, member: nextcord.Member):
        await interaction.response.send_message(embed=self.UserInfoEmbed(member))
        return

    @nextcord.slash_command(name="user", description="ユーザー情報表示", guild_ids=n_fc.GUILD_IDS)
    async def user_slash(
        self,
        interaction: Interaction,
        user: nextcord.User = SlashOption(
            name="user",
            description="情報を表示するユーザー",
            required=False
        )
    ):
        if user is None:
            user = interaction.user
        await interaction.response.send_message(embed=self.UserInfoEmbed(user))
        return

    @commands.command(name="d", help="""\
ユーザーの情報を表示します。
引数を指定せずに`n!d`とだけ指定するとあなた自身の情報を表示します。
`n!d [ユーザーID]`という風に指定すると、そのユーザーの情報を表示することが出来ます。
ユーザーIDの指定方法は...多分調べれば出てきます。
**メンションでも指定できますが、いざこざとかにつながるかもしれないのでしないほうが得策です。**""")
    async def d(self, ctx: commands.Context):
        arg = ctx.message.content.split(" ", 1)
        if len(arg) == 1:
            user = await self.bot.fetch_user(ctx.author.id)
            await ctx.reply(embed=self.UserInfoEmbed(user))
            return
        else:
            check_id = int(
                "".join(re.findall(r'[0-9]', arg[1])))
            try:
                user = await self.bot.fetch_user(check_id)
                await ctx.reply(embed=self.UserInfoEmbed(user))
                return
            except Exception:
                try:
                    channel = await self.bot.fetch_channel(check_id)
                    if type(channel) == nextcord.channel.TextChannel:
                        embed = nextcord.Embed(
                            title="TextChannel Info",
                            description=f"名前:`{channel.name}`\nID:`{channel.id}`\nカテゴリ:`{channel.category}`\n{(lambda x: '__NSFW__' if x else '')(channel.is_nsfw())}\n",
                            color=0x00ff00
                        )
                        (
                            lambda x: embed.add_field(
                                name="チャンネルトピック",
                                value=f"```\n{x}```"
                            ) if x is not None else None
                        )(
                            channel.topic
                        )
                    elif type(channel) == nextcord.channel.VoiceChannel:
                        embed = nextcord.Embed(
                            title="VoiceChannel Info",
                            description=f"名前:`{channel.name}`\nID:`{channel.id}`\nカテゴリ:`{channel.category}`\nビットレート:`{channel.bitrate/1000}`kbps\n人数:`{len(channel.voice_states.keys())}/{channel.user_limit}`人",
                            color=0x00ff00
                        )
                    elif type(channel) == nextcord.channel.StageChannel:
                        embed = nextcord.Embed(
                            title="StageChannel Info",
                            description=f"名前:`{channel.name}`\nID:`{channel.id}`\nカテゴリ:`{channel.category}`\nビットレート:`{channel.bitrate/1000}`kbps\n人数:`{len(channel.voice_states.keys())}/{channel.user_limit}`人",
                            color=0x00ff00
                        )
                        (
                            lambda x: embed.add_field(
                                name="チャンネルトピック",
                                value=f"```\n{x}```"
                            ) if x is not None else None
                        )(
                            channel.topic
                        )
                    elif type(channel) == nextcord.channel.CategoryChannel:
                        embed = nextcord.Embed(
                            title="CategoryChannel Info",
                            description=f"名前:`{channel.name}`\nID:`{channel.id}`\nテキストチャンネル数:`{len(channel.text_channels)}`\nボイスチャンネル数:`{len(channel.voice_channels)}`\nステージチャンネル数:`{len(channel.stage_channels)}`",
                            color=0x00ff00
                        )
                    await ctx.reply(embed=embed)
                    return
                except Exception:
                    try:
                        # Forbidden.....?????
                        guild = await self.bot.fetch_guild(check_id)
                        embed = nextcord.Embed(
                            title="Guild Info",
                            description=f"名前:`{guild.name}`\nID:`{guild.id}`\n人数:`{len(guild.members)}`人(そのうちのBOT数:`{len(guild.bots)}`)\nオーナー:{guild.owner.mention}",
                            color=0x00ff00
                        )
                        (
                            lambda x: embed.add_field(
                                name="説明文",
                                value=f"```\n{x}```"
                            ) if x is not None else None
                        )(
                            guild.description
                        )
                        await ctx.reply(embed=embed)
                        return
                    except Exception:
                        await ctx.reply(embed=nextcord.Embed(title="Error", description="ユーザー、チャンネル、またはサーバーのデータが取得できませんでした。", color=0xff0000))
                        return

    @nextcord.slash_command(name="rk", description="ロールキーパー機能の設定", guild_ids=n_fc.GUILD_IDS)
    async def rk_slash(
        self,
        interaction: Interaction,
        SettingValue: int = SlashOption(
            name="setting_value",
            description="設定値",
            required=True,
            choices={"有効にする": 1, "無効にする": 0}
        )
    ):
        if admin_check.admin_check(interaction.guild, interaction.user):
            await database.default_pull(self.client, RoleKeeper)
            if interaction.guild.id in RoleKeeper.value:
                RoleKeeper.value[interaction.guild.id]["rk"] = SettingValue
                await interaction.response.send_message(embed=nextcord.Embed(title="Role Keeper", description="設定を変更しました。", color=0x00ff00))
            else:
                RoleKeeper.value[interaction.guild.id] = {"rk": SettingValue}
                await interaction.response.send_message(embed=nextcord.Embed(title="Role Keeper", description="設定を変更しました。", color=0x00ff00))
            await database.default_push(self.client, RoleKeeper)
            return
        else:
            await interaction.response.send_message(embed=nextcord.Embed(title="Error", description="権限がありません。", color=0xff0000))
            return

    @commands.command(name="rk", help="""\
ロールキーパー機能です。
大前提、**ちゃんと機能するとは思わないでください。**
`n!rk [on/off]`でロールキーパー機能の設定が可能です。ただ、ロールキーパー機能を有効にするには`n!ui`の、ユーザー情報表示を有効にしないと有効になりません。""")
    async def rk(self, ctx: commands.Context):
        if admin_check.admin_check(ctx.guild, ctx.author):
            if ctx.message.content == f"{self.bot.command_prefix}rk":
                embed = nextcord.Embed(
                    title="ロールキーパー",
                    description=f"`{self.bot.command_prefix}rk [on/off]`",
                    color=0x00ff00
                )
                await database.default_pull(self.client, RoleKeeper)
                if ctx.guild.id not in RoleKeeper.value:
                    RoleKeeper.value[ctx.guild.id] = {"rk": 0}
                    await database.default_push(self.client, RoleKeeper)
                if RoleKeeper.value[ctx.guild.id]["rk"] == 0:
                    role_bool = "無効"
                else:
                    role_bool = "有効"
                embed.add_field(
                    name="ロールキーパーの状態",
                    value=f"ロールキーパーは現在{role_bool}です"
                )
                await ctx.reply(embed=embed)
                return
            if ctx.message.content.split(" ", 1)[1] in n_fc.on_ali:
                # ロールキーパーオンにしやがれ
                await database.default_pull(self.client, RoleKeeper)
                if ctx.guild.id not in RoleKeeper.value:
                    RoleKeeper.value[ctx.guild.id] = {"rk": 1}
                else:
                    RoleKeeper.value[ctx.guild.id]["rk"] = 1
            elif ctx.message.content.split(" ", 1)[1] in n_fc.off_ali:
                # ロールキーパーオフにしやがれ
                if ctx.guild.id not in RoleKeeper.value:
                    RoleKeeper.value[ctx.guild.id] = {"rk": 0}
                else:
                    RoleKeeper.value[ctx.guild.id]["rk"] = 0
            else:
                await ctx.reply(f"値が不正です。\n`{self.bot.command_prefix}rk [on/off]`")
                return
            await database.default_push(self.client, RoleKeeper)
            await ctx.reply("ロールキーパーの設定を更新しました。")
            return
        else:
            await ctx.reply("権限がありません。")

    async def ui_config(self, bot: commands.Bot, client: HTTP_db.Client, interaction: Interaction or commands.Context, type: int, guild_id: int, channel: nextcord.channel):
        await database.default_pull(client, WelcomeInfo)
        if type == SET:
            try:
                WelcomeInfo.value[guild_id] = channel.id
                CHANNEL = await bot.fetch_channel(WelcomeInfo.value[guild_id])
                await CHANNEL.send("このチャンネルが、ユーザー情報表示チャンネルとして指定されました。")
                await slash_tool.messages.mreply(interaction, "", embed=nextcord.Embed(title="ユーザー情報表示設定", description=f"<#{channel.id}>に指定されました。", color=0x00ff00), ephemeral=True)
            except Exception as err:
                await slash_tool.messages.mreply(interaction, "", embed=nextcord.Embed(title="ユーザー情報表示設定", description=f"エラーが発生しました。\n```\n{err}```", color=0xff000), ephemeral=True)
        elif type == DEL:
            try:
                if guild_id not in WelcomeInfo.value:
                    await slash_tool.messages.mreply(interaction, "", embed=nextcord.Embed(title="ユーザー情報表示設定", description=f"このサーバーには登録されていません。", color=0xff0000), ephemeral=True)
                    return
                del WelcomeInfo.value[guild_id]
                await slash_tool.messages.mreply(interaction, "", embed=nextcord.Embed(title="ユーザー情報表示設定", description=f"設定を削除しました。", color=0x00ff00), ephemeral=True)
            except Exception as err:
                await slash_tool.messages.mreply(interaction, "", embed=nextcord.Embed(title="ユーザー情報表示設定", description=f"エラーが発生しました。\n```\n{err}```", color=0xff000), ephemeral=True)
        elif type == STATUS:
            if guild_id not in WelcomeInfo.value:
                await slash_tool.messages.mreply(interaction, "", embed=nextcord.Embed(title="ユーザー情報表示設定", description=f"サーバーで設定は`無効`です", color=0x00ff00), ephemeral=True)
            else:
                await slash_tool.messages.mreply(interaction, "", embed=nextcord.Embed(title="ユーザー情報表示設定", description=f"サーバーで設定は`有効`です\n設定チャンネル: <#{n_fc.welcome_id_list[guild_id]}>", color=0x00ff00), ephemeral=True)
            return
        await database.default_push(client, WelcomeInfo)

    @nextcord.slash_command(name="ui", description="サーバー加入/離脱した場合にそのユーザーの情報を表示します", guild_ids=n_fc.GUILD_IDS)
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
        if admin_check.admin_check(interaction.guild, interaction.user):
            await self.ui_config(self.bot, self.client, interaction, SET, interaction.guild.id, channel)
        else:
            await interaction.response.send_message("管理者権限がありません。", ephemeral=True)
        return

    @ui_slash.subcommand(name="del", description="ユーザー表示チャンネル設定を削除します")
    async def del_slash(
        self,
        interaction: Interaction
    ):
        if admin_check.admin_check(interaction.guild, interaction.user):
            await self.ui_config(self.bot, self.client, interaction, DEL, interaction.guild.id, None)
        else:
            await interaction.response.send_message("管理者権限がありません。", ephemeral=True)
        return

    @ui_slash.subcommand(name="status", description="ユーザー表示チャンネル設定を確認します")
    async def status_slash(
        self,
        interaction: Interaction
    ):
        if admin_check.admin_check(interaction.guild, interaction.user):
            await self.ui_config(self.bot, self.client, interaction, STATUS, interaction.guild.id, None)
        else:
            await interaction.response.send_message("管理者権限がありません。", ephemeral=True)
        return

    @commands.command(name="ui", help="""\
誰かがDiscordサーバーに加入/離脱した際に、指定したチャンネルにそのユーザーの情報を表示します。
それだけです。

`n!ui set [チャンネルID]`
`n!ui del`""")
    async def ui(self, ctx: commands.Context):
        if admin_check.admin_check(ctx.guild, ctx.author):
            mes_arg = ctx.message.content.split(" ")
            if len(mes_arg) == 1:
                await self.ui_config(self.bot, self.client, ctx, STATUS, ctx.guild.id, None)
                return
            elif mes_arg[1] == "set":
                set_id = int("".join(re.findall(r'[0-9]', mes_arg[2])))
                channel = await self.bot.fetch_channel(set_id)
                await self.ui_config(self.bot, self.client, ctx, SET, ctx.guild.id, channel)
                return
            elif mes_arg[1] == "del":
                await self.ui_config(self.bot, self.client, ctx, DEL, ctx.guild.id, None)
                return
            else:
                await self.ui_config(self.bot, self.client, ctx, STATUS, ctx.guild.id, None)

        else:
            await ctx.reply(embed=nextcord.Embed(title="Error", description=f"管理者権限がありません。", color=0xff0000))
            return


def setup(bot, **kwargs):
    bot.add_cog(user(bot, **kwargs))
