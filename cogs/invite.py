import asyncio
import copy
import logging
import os
import sys
import traceback
from re import compile

import nextcord
from nextcord import Interaction, SlashOption, ChannelType
from nextcord.ext import commands, tasks

from util import admin_check, n_fc, eh, database, dict_list

import HTTP_db

inviteUrlTemplate = compile(r'https://discord.gg/([0-9a-zA-Z]+)')

# inviter

class InviteData:
    name = "invite_data"
    value = {}
    default = {}
    value_type = database.CHANNEL_VALUE

async def fetch_invite(client: HTTP_db.Client, discord_invites: list, guild_id: int):
    await database.default_pull(client, InviteData)
    if guild_id not in InviteData.value.keys():
        InviteData.value[guild_id] = {i.url: [None, i.uses] for i in discord_invites}
    else:
        for i in discord_invites:
            if i.url not in InviteData.value[guild_id].keys():
                InviteData.value[guild_id][i.url] = [None, i.uses]
            if InviteData.value[guild_id][i.url][1] != i.uses:
                InviteData.value[guild_id][i.url][1] = i.uses
        tmp_dict = copy.deepcopy(InviteData.value)
        for key in tmp_dict[guild_id].keys():
            if key not in [i.url for i in discord_invites]:
                del InviteData.value[guild_id][key]
    await database.default_push(client, InviteData)
    return

class Invite(commands.Cog):
    def __init__(self, bot: commands.Bot, **kwargs):
        self.bot = bot
        self.client = kwargs["client"]


    @commands.bot_has_permissions(manage_guild=True)
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
            description="名前を付ける招待リンクまたは招待コードです [https://discord.gg/aBcD1234]or[aBcD1234]",
            required=True
        )
    ):
        await interaction.response.defer()
        if admin_check.admin_check(interaction.guild, interaction.member):
            if inviteUrlTemplate.search(InviteURL) is None:
                InviteURL = f"https://discord.gg/{InviteURL}"
            else:
                InviteURL = inviteUrlTemplate.search(InviteURL).group()
            await fetch_invite(self.client, await interaction.guild.invites(), interaction.guild.id)
            await database.default_pull(self.client, InviteData)
            if InviteURL in InviteData.value[interaction.guild.id]:
                InviteData.value[interaction.guild.id][InviteURL][0] = InviteAlias
                await interaction.followup.send(embed=nextcord.Embed(title="InviteURL", description=f"招待リンク`{InviteURL}`を`{InviteAlias}`として設定しました。", color=0x00FF00))
            else:
                await interaction.followup.send(embed=nextcord.Embed(title="エラー", description=f"招待リンク`{InviteURL}`が見つかりませんでした。", color=0xFF0000))
            await database.default_push(self.client, InviteData)
        else:
            await interaction.followup.send(embed=nextcord.Embed(title="エラー", description=f"あなたは管理者ではありません。", color=0xFF0000))
        return

    @invite_slash.subcommand(name="del", description="招待リンクの名前を削除します。")
    async def del_invite_slash(
        self,
        interaction: Interaction,
        InviteURL: str = SlashOption(
            name="invite_url",
            description="名前を削除する招待リンクまたは招待コードです [https://discord.gg/aBcD1234]or[aBcD1234]",
            required=True
        )
    ):
        await interaction.response.defer()
        if admin_check.admin_check(interaction.guild, interaction.member):
            if inviteUrlTemplate.search(InviteURL) is None:
                InviteURL = f"https://discord.gg/{InviteURL}"
            else:
                InviteURL = inviteUrlTemplate.search(InviteURL).group()
            await fetch_invite(self.client, await interaction.guild.invites(), interaction.guild.id)
            await database.default_pull(self.client, InviteData)
            if InviteURL in InviteData.value[interaction.guild.id]:
                InviteData.value[interaction.guild.id][InviteURL][0] = None
                await interaction.followup.send(embed=nextcord.Embed(title="InviteURL", description=f"招待リンク`{InviteURL}`の名前を削除しました。", color=0x00FF00))
            else:
                await interaction.followup.send(embed=nextcord.Embed(title="エラー", description=f"招待リンク`{InviteURL}`が見つかりませんでした。", color=0xFF0000))
            await database.default_push(self.client, InviteData)
        else:
            await interaction.followup.send(embed=nextcord.Embed(title="エラー", description=f"あなたは管理者ではありません。", color=0xFF0000))
        return

    @invite_slash.subcommand(name="list", description="招待リンクの一覧を表示します。")
    async def list_invite_slash(self, interaction: Interaction):
        await interaction.response.defer()
        Invites = await interaction.guild.invites()
        if len(Invites) == 0:
            await interaction.followup.send(embed=nextcord.Embed(title="招待リスト", description="このサーバーでは招待が作成されていません。", color=0x00ff00))
            return
        await fetch_invite(self.client, Invites, interaction.guild.id)
        await database.default_pull(self.client, InviteData)
        EmbedDescription = ""
        for key, value in InviteData.value[interaction.guild.id].items():
            if value[0] is not None:
                EmbedDescription += f"[{value[0]}]({key}) - `{value[1]}`回\n"
            else:
                EmbedDescription += f"[{key}]({key}) - `{value[1]}`回\n"
        embed = nextcord.Embed(
            title="招待リスト",
            description=EmbedDescription,
            color=0x00FF00
        )
        await interaction.followup.send(embed=embed)
        return

    @commands.bot_has_permissions(manage_guild=True)
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
        args = ctx.message.content.split(" ", 3) # n!invite set url aliase
        Invites = await ctx.guild.invites()
        if len(args) == 1:
            if len(Invites) == 0:
                await ctx.reply(embed=nextcord.Embed(title="招待リスト", description="このサーバーでは招待が作成されていません。", color=0x00ff00))
                return
            await fetch_invite(self.client, Invites, ctx.guild.id)
            await database.default_pull(self.client, InviteData)
            EmbedDescription = ""
            for key, value in InviteData.value[ctx.guild.id].items():
                if value[0] is not None:
                    EmbedDescription += f"[{value[0]}]({key}) - `{value[1]}`回\n"
                else:
                    EmbedDescription += f"[{key}]({key}) - `{value[1]}`回\n"
            embed = nextcord.Embed(
                title="招待リスト",
                description=EmbedDescription,
                color=0x00FF00
            )
            await ctx.reply(embed=embed)
            return

        elif len(args) == 2:
            if args[1] == "set":
                await ctx.reply(embed=nextcord.Embed(title="エラー", description=f"引数が足りません。\n`{self.bot.command_prefix}invite set [招待リンクまたは招待コード] [名前]`", color=0xFF0000))
            elif args[1] == "del":
                await ctx.reply(embed=nextcord.Embed(title="エラー", description=f"引数が足りません。\n`{self.bot.command_prefix}invite del [招待リンクまたは招待コード]`", color=0xFF0000))
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
                    await fetch_invite(self.client, Invites, ctx.guild.id)
                    await database.default_pull(self.client, InviteData)
                    if InviteURL in InviteData.value[ctx.guild.id]:
                        InviteData.value[ctx.guild.id][InviteURL][0] = None
                        await ctx.reply(embed=nextcord.Embed(title="InviteURL", description=f"招待リンク`{InviteURL}`の名前を削除しました。", color=0x00FF00))
                    else:
                        await ctx.reply(embed=nextcord.Embed(title="エラー", description=f"招待リンク`{InviteURL}`が見つかりませんでした。", color=0xFF0000))
                    await database.default_push(self.client, InviteData)
                else:
                    await ctx.reply(embed=nextcord.Embed(title="エラー", description=f"あなたは管理者ではありません。", color=0xFF0000))
            elif args[1] == "set":
                await ctx.reply(embed=nextcord.Embed(title="エラー", description=f"引数が足りません。\n`{self.bot.command_prefix}invite set [招待リンクまたは招待コード] [名前]`", color=0xFF0000))
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
                    await fetch_invite(self.client, Invites, ctx.guild.id)
                    await database.default_pull(self.client, InviteData)
                    if InviteURL in InviteData.value[ctx.guild.id]:
                        InviteData.value[ctx.guild.id][InviteURL][0] = Alias
                        await ctx.reply(embed=nextcord.Embed(title="InviteURL", description=f"招待リンク`{InviteURL}`を`{Alias}`として設定しました。", color=0x00FF00))
                    else:
                        await ctx.reply(embed=nextcord.Embed(title="エラー", description=f"招待リンク`{InviteURL}`が見つかりませんでした。", color=0xFF0000))
                    await database.default_push(self.client, InviteData)
                else:
                    await ctx.reply(embed=nextcord.Embed(title="エラー", description=f"あなたは管理者ではありません。", color=0xFF0000))
            elif args[1] == "del":
                await ctx.reply(embed=nextcord.Embed(title="エラー", description=f"引数が足りません。\n`{self.bot.command_prefix}invite del [招待リンクまたは招待コード]`", color=0xFF0000))
            else:
                await ctx.reply(embed=nextcord.Embed(title="エラー", description=f"不明な引数`{args[1]}`です。", color=0xFF0000))

        else:
            await ctx.reply(embed=nextcord.Embed(title="エラー", description=f"多分引数が間違ってます。", color=0xFF0000))

    @commands.bot_has_permissions(manage_guild=True)
    @commands.Cog.listener()
    async def on_invite_create(self, invite: nextcord.Invite):
        await fetch_invite(self.client, await invite.guild.invites(), invite.guild.id)


    @commands.bot_has_permissions(manage_guild=True)
    @commands.Cog.listener()
    async def on_invite_delete(self, invite: nextcord.Invite):
        await fetch_invite(self.client, await invite.guild.invites(), invite.guild.id)
        await database.default_pull(self.client, InviteData)
        if invite.url in InviteData.value[invite.guild.id]:
            del InviteData.value[invite.guild.id][invite.url]
        await database.default_push(self.client, InviteData)


def setup(bot, **kwargs):
    bot.add_cog(Invite(bot, **kwargs))
