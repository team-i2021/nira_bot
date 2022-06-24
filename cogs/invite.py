import asyncio
import logging
import os
import sys
import traceback
from re import compile

import nextcord
from nextcord import Interaction, SlashOption, ChannelType
from nextcord.ext import commands

from util import admin_check, n_fc, eh, database

inviteUrlTemplate = compile(r'https://discord.gg/([0-9a-zA-Z]+)')

# inviter

DBS = database.openSheet()
DATABASE_KEY = "B7"


def readValue():
    data = database.readValue(DBS, DATABASE_KEY)
    tmp = {}
    for key, value in data.items():
        tmp[int(key)] = value
    data = tmp
    return data


class Invite(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @nextcord.slash_command(name="invite", description="Set alias for invite url.", guild_ids=n_fc.GUILD_IDS)
    async def invite_slash(
            self,
            interaction: Interaction
        ):
        pass

    @invite_slash.subcommand(name="set", description="招待リンクに名前を付けます。")
    async def set_invite_slash(
            self,
            interaction: Interaction,
            InviteAlias: str = SlashOption(
                name="invite_alias",
                description="招待リンクにつける名前です",
                required=True
            ),
            InviteURL: str = SlashOption(
                name="invite_url",
                description="名前を付ける招待リンクまたは招待コードです [https://discord.gg/abcD1234]or[abcD1234]",
                required=True
            )
        ):
        await interaction.response.defer()
        if admin_check.admin_check(interaction.guild, interaction.member):
            if inviteUrlTemplate.search(InviteURL) is None:
                InviteURL = f"https://discord.gg/{InviteURL}"
            else:
                InviteURL = inviteUrlTemplate.search(InviteURL).group()
            InviteData = readValue()
            if interaction.guild.id not in InviteData:
                InviteData[interaction.guild.id] = {i.url: [None, i.uses] for i in await interaction.guild.invites()}
            if InviteURL in InviteData[interaction.guild.id]:
                InviteData[interaction.guild.id][InviteURL][0] = InviteAlias
                await interaction.followup.send(embed=nextcord.Embed(title="InviteURL", description=f"招待リンク`{InviteURL}`を`{InviteAlias}`として設定しました。", color=0x00FF00), ephemeral=True)
            else:
                await interaction.followup.send(embed=nextcord.Embed(title="エラー", description=f"招待リンク`{InviteURL}`が見つかりませんでした。", color=0xFF0000), ephemeral=True)
        else:
            await interaction.followup.send(embed=nextcord.Embed(title="エラー", description=f"あなたは管理者ではありません。", color=0xFF0000), ephemeral=True)
        database.writeValue(DBS, DATABASE_KEY, InviteData)
        return

    @invite_slash.subcommand(name="del", description="招待リンクの名前を削除します。")
    async def del_invite_slash(
            self,
            interaction: Interaction,
            InviteURL: str = SlashOption(
                name="invite_url",
                description="名前を削除する招待リンクまたは招待コードです [https://discord.gg/abcD1234]or[abcD1234]",
                required=True
            )
        ):
        await interaction.response.defer()
        if admin_check.admin_check(interaction.guild, interaction.member):
            if inviteUrlTemplate.search(InviteURL) is None:
                InviteURL = f"https://discord.gg/{InviteURL}"
            else:
                InviteURL = inviteUrlTemplate.search(InviteURL).group()
            InviteData = readValue()
            if interaction.guild.id not in InviteData:
                InviteData[interaction.guild.id] = {i.url: [None, i.uses] for i in await interaction.guild.invites()}
            if InviteURL in InviteData[interaction.guild.id]:
                InviteData[interaction.guild.id][InviteURL][0] = None

                await interaction.followup.send(embed=nextcord.Embed(title="InviteURL", description=f"招待リンク`{InviteURL}`の名前を削除しました。", color=0x00FF00), ephemeral=True)
            else:
                await interaction.followup.send(embed=nextcord.Embed(title="エラー", description=f"招待リンク`{InviteURL}`が見つかりませんでした。", color=0xFF0000), ephemeral=True)
        else:
            await interaction.followup.send(embed=nextcord.Embed(title="エラー", description=f"あなたは管理者ではありません。", color=0xFF0000), ephemeral=True)
        database.writeValue(DBS, DATABASE_KEY, InviteData)
        return

    @invite_slash.subcommand(name="list", description="招待リンクの一覧を表示します。")
    async def list_invite_slash(self, interaction:Interaction):
        await interaction.response.defer()
        InviteData = readValue()
        if interaction.guild.id not in InviteData:
            InviteData[interaction.guild.id] = {i.url: [None, i.uses] for i in await interaction.guild.invites()}
            database.writeValue(DBS, DATABASE_KEY, InviteData)
        EmbedDescription = ""
        for key, value in InviteData[interaction.guild.id].items():
            if value[0] is not None:
                EmbedDescription += f"[{value[0]}]({key}) - `{value[1]}`回\n"
            else:
                EmbedDescription += f"[{key}]({key}) - `{value[1]}`回\n"
        embed = nextcord.Embed(title="招待リスト", description=EmbedDescription, color=0x00FF00)
        await interaction.followup.send(embed=embed)
        return

    @commands.command(name="invite", help="""\
招待リンク表示

引数を指定せずに`n!invite`とだけすると、招待リンクの一覧になります。

・使い方
招待リンクに名前を付けることができます。
招待リンクにつけられた名前は、にらBOT内でのみ利用され、`n!ui`のユーザー参加時情報表示機能などで、表示されます。

`n!invite set [招待リンクまたは招待コード] [名前]`(招待リンクへの名前設定)
`n!invite del [招待リンクまたは招待コード]`(招待リンクの名前の削除)

・例
`n!invite set awfFpCYTcP めいん`
`n!invite del https://discord.gg/awfFpCYTcP`""")
    async def invite(self, ctx: commands.Context):
        args = ctx.message.content.split(" ", 3)
        if len(args) == 1:
            InviteData = readValue()
            if ctx.guild.id not in InviteData:
                InviteData[ctx.guild.id] = {i.url: [None, i.uses] for i in await ctx.guild.invites()}
                database.writeValue(DBS, DATABASE_KEY, InviteData)
            EmbedDescription = ""
            for key, value in InviteData[ctx.guild.id].items():
                if value[0] is not None:
                    EmbedDescription += f"[{value[0]}]({key}) - `{value[1]}`回\n"
                else:
                    EmbedDescription += f"[{key}]({key}) - `{value[1]}`回\n"
            embed = nextcord.Embed(title="招待リスト", description=EmbedDescription, color=0x00FF00)
            await ctx.reply(embed=embed)
            return

        elif len(args) == 2:
            if args[1] == "set":
                await ctx.reply(embed=nextcord.Embed(title="エラー", description="引数が足りません。\n`n!invite set [招待リンクまたは招待コード] [名前]`", color=0xFF0000))
            elif args[1] == "del":
                await ctx.reply(embed=nextcord.Embed(title="エラー", description="引数が足りません。\n`n!invite del [招待リンクまたは招待コード]`", color=0xFF0000))
            else:
                await ctx.reply(embed=nextcord.Embed(title="エラー", description=f"不明な引数`{args[1]}`です。", color=0xFF0000))
            return

        elif len(args) == 3:
            if args[1] == "del":
                if admin_check.admin_check(ctx.guild, ctx.author):
                    InviteURL = args[2]
                    if inviteUrlTemplate.search(InviteURL) is None:
                        InviteURL = f"https://discord.gg/{InviteURL}"
                    else:
                        InviteURL = inviteUrlTemplate.search(InviteURL).group()
                    InviteData = readValue()
                    if ctx.guild.id not in InviteData:
                        InviteData[ctx.guild.id] = {i.url: [None, i.uses] for i in await ctx.guild.invites()}
                    if InviteURL in InviteData[ctx.guild.id]:
                        InviteData[ctx.guild.id][InviteURL][0] = None

                        await ctx.reply(embed=nextcord.Embed(title="InviteURL", description=f"招待リンク`{InviteURL}`の名前を削除しました。", color=0x00FF00))
                    else:
                        await ctx.reply(embed=nextcord.Embed(title="エラー", description=f"招待リンク`{InviteURL}`が見つかりませんでした。", color=0xFF0000))
                else:
                    await ctx.reply(embed=nextcord.Embed(title="エラー", description=f"あなたは管理者ではありません。", color=0xFF0000))
                database.writeValue(DBS, DATABASE_KEY, InviteData)
            elif args[1] == "set":
                await ctx.reply(embed=nextcord.Embed(title="エラー", description="引数が足りません。\n`n!invite set [招待リンクまたは招待コード] [名前]`", color=0xFF0000))
            else:
                await ctx.reply(embed=nextcord.Embed(title="エラー", description=f"不明な引数`{args[1]}`です。", color=0xFF0000))
            return

        elif len(args) == 4:
            if args[1] == "set":
                if admin_check.admin_check(ctx.guild, ctx.author):
                    InviteURL = args[2]
                    Alias = args[3]
                    if inviteUrlTemplate.search(InviteURL) is None:
                        InviteURL = f"https://discord.gg/{InviteURL}"
                    else:
                        InviteURL = inviteUrlTemplate.search(InviteURL).group()
                    InviteData = readValue()
                    if ctx.guild.id not in InviteData:
                        InviteData[ctx.guild.id] = {i.url: [None, i.uses] for i in await ctx.guild.invites()}
                    if InviteURL in InviteData[ctx.guild.id]:
                        InviteData[ctx.guild.id][InviteURL][0] = Alias
                        await ctx.reply(embed=nextcord.Embed(title="InviteURL", description=f"招待リンク`{InviteURL}`を`{Alias}`として設定しました。", color=0x00FF00))
                    else:
                        await ctx.reply(embed=nextcord.Embed(title="エラー", description=f"招待リンク`{InviteURL}`が見つかりませんでした。", color=0xFF0000))
                else:
                    await ctx.reply(embed=nextcord.Embed(title="エラー", description=f"あなたは管理者ではありません。", color=0xFF0000))
            elif args[1] == "del":
                await ctx.reply(embed=nextcord.Embed(title="エラー", description="引数が足りません。\n`n!invite del [招待リンクまたは招待コード]`", color=0xFF0000))
            else:
                await ctx.reply(embed=nextcord.Embed(title="エラー", description=f"不明な引数`{args[1]}`です。", color=0xFF0000))
            database.writeValue(DBS, DATABASE_KEY, InviteData)

        else:
            await ctx.reply(embed=nextcord.Embed(title="エラー", description=f"多分引数が間違ってます。", color=0xFF0000))


def setup(bot):
    bot.add_cog(Invite(bot))
