import asyncio
import copy
from re import compile

import nextcord
from nextcord import Interaction, SlashOption
from nextcord.ext import commands, application_checks

from util import n_fc
from util.nira import NIRA

import HTTP_db

from motor import motor_asyncio

inviteUrlTemplate = compile(r'https://discord.gg/([0-9a-zA-Z]+)')

# inviter



class Invite(commands.Cog):
    def __init__(self, bot: NIRA, **kwargs):
        self.bot = bot
        self.collection: motor_asyncio.AsyncIOMotorCollection = self.bot.database["invite_data"]

    
    async def fetch_invite(self, discord_invites: list, guild_id: int):
        result = await self.collection.find_one({"guild_id": guild_id})
        if result is None:
            result = {invite.url: [None, invite.uses] for invite in discord_invites}
        else:
            for invite in discord_invites:
                if invite.url not in result.keys():
                    result[invite.url] = [None, invite.uses]
                if result[invite.url][1] != invite.uses:
                    result[invite.url][1] = invite.uses
            tmp_dict = copy.deepcopy(result)
            for key in tmp_dict.keys():
                if key not in [invite.url for invite in discord_invites]:
                    del result[key]

        await self.collection.update_one({"guild_id": guild_id}, {"$set": result}, upsert=True)


    @commands.bot_has_permissions(manage_guild=True)
    @nextcord.slash_command(name="invite", description="Set alias for invite url.", guild_ids=n_fc.GUILD_IDS)
    async def invite_slash(
            self,
            interaction: Interaction
        ):
        pass


    @application_checks.has_permissions(manage_guild=True)
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
        if inviteUrlTemplate.search(InviteURL) is None:
            InviteURL = f"https://discord.gg/{InviteURL}"
        else:
            InviteURL = inviteUrlTemplate.search(InviteURL).group()
        await self.fetch_invite(await interaction.guild.invites(), interaction.guild.id)
        InviteData = await self.collection.find_one({"guild_id": interaction.guild.id})
        if InviteURL in InviteData:
            InviteData[InviteURL][0] = InviteAlias
            await interaction.send(embed=nextcord.Embed(title="InviteURL", description=f"招待リンク`{InviteURL}`を`{InviteAlias}`として設定しました。", color=0x00FF00))
        else:
            await interaction.send(embed=nextcord.Embed(title="エラー", description=f"招待リンク`{InviteURL}`が見つかりませんでした。", color=0xFF0000))
        asyncio.ensure_future(self.collection.update_one({"guild_id": interaction.guild.id}, {"$set": InviteData}, upsert=True))


    @application_checks.has_permissions(manage_guild=True)
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
        if inviteUrlTemplate.search(InviteURL) is None:
            InviteURL = f"https://discord.gg/{InviteURL}"
        else:
            InviteURL = inviteUrlTemplate.search(InviteURL).group()
        await self.fetch_invite(await interaction.guild.invites(), interaction.guild.id)
        InviteData = await self.collection.find_one({"guild_id": interaction.guild.id})
        if InviteURL in InviteData:
            InviteData[InviteURL][0] = None
            await interaction.send(embed=nextcord.Embed(title="InviteURL", description=f"招待リンク`{InviteURL}`の名前を削除しました。", color=0x00FF00))
        else:
            await interaction.send(embed=nextcord.Embed(title="エラー", description=f"招待リンク`{InviteURL}`が見つかりませんでした。", color=0xFF0000))
        asyncio.ensure_future(self.collection.update_one({"guild_id": interaction.guild.id}, {"$set": InviteData}, upsert=True))


    @invite_slash.subcommand(name="list", description="招待リンクの一覧を表示します。")
    async def list_invite_slash(self, interaction: Interaction):
        await interaction.response.defer()
        Invites = await interaction.guild.invites()
        if len(Invites) == 0:
            await interaction.followup.send(embed=nextcord.Embed(title="招待リスト", description="このサーバーでは招待が作成されていません。", color=0x00ff00))
            return
        await self.fetch_invite(Invites, interaction.guild.id)
        InviteData = await self.collection.find_one({"guild_id": interaction.guild.id})
        EmbedDescription = ""
        for key, value in InviteData.items():
            if value[0] is not None:
                EmbedDescription += f"[{value[0]}]({key}) - `{value[1]}`回\n"
            else:
                EmbedDescription += f"[{key}]({key}) - `{value[1]}`回\n"
        embed = nextcord.Embed(
            title="招待リスト",
            description=EmbedDescription,
            color=0x00FF00
        )
        await interaction.send(embed=embed)

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
    async def invite(self, ctx: commands.Context, setting: str | None = None, InviteURL: str | None = None, aliase: str | None = None):

        Invites = await ctx.guild.invites()

        if setting is None:
            if len(Invites) == 0:
                await ctx.reply(embed=nextcord.Embed(title="招待リスト", description="このサーバーでは招待が作成されていません。", color=0x00ff00))
                return
            await self.fetch_invite(Invites, ctx.guild.id)
            InviteData = await self.collection.find_one({"guild_id": ctx.guild.id})
            EmbedDescription = ""
            for key, value in InviteData.items():
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

        elif setting == "set":
            if InviteURL is None or aliase is None:
                await ctx.reply(embed=nextcord.Embed(title="エラー", description="引数が不足しています。", color=0xFF0000))
            else:
                if inviteUrlTemplate.search(InviteURL) is None:
                    InviteURL = f"https://discord.gg/{InviteURL}"
                else:
                    InviteURL = inviteUrlTemplate.search(InviteURL).group()
                await self.fetch_invite(Invites, ctx.guild.id)
                InviteData = await self.collection.find_one({"guild_id": ctx.guild.id})
                if InviteURL in InviteData:
                    InviteData[InviteURL][0] = aliase
                    await ctx.reply(embed=nextcord.Embed(title="InviteURL", description=f"招待リンク`{InviteURL}`を`{aliase}`として設定しました。", color=0x00FF00))
                else:
                    await ctx.reply(embed=nextcord.Embed(title="エラー", description=f"招待リンク`{InviteURL}`が見つかりませんでした。", color=0xFF0000))
                asyncio.ensure_future(self.collection.update_one({"guild_id": ctx.guild.id}, {"$set": InviteData}))

        elif setting == "del":
            if InviteURL is None:
                await ctx.reply(embed=nextcord.Embed(title="エラー", description="引数が不足しています。", color=0xFF0000))
            else:
                if inviteUrlTemplate.search(InviteURL) is None:
                    InviteURL = f"https://discord.gg/{InviteURL}"
                else:
                    InviteURL = inviteUrlTemplate.search(InviteURL).group()
                await self.fetch_invite(Invites, ctx.guild.id)
                InviteData = await self.collection.find_one({"guild_id": ctx.guild.id})
                if InviteURL in InviteData:
                    InviteData[InviteURL][0] = None
                    await ctx.reply(embed=nextcord.Embed(title="InviteURL", description=f"招待リンク`{InviteURL}`の名前を削除しました。", color=0x00FF00))
                else:
                    await ctx.reply(embed=nextcord.Embed(title="エラー", description=f"招待リンク`{InviteURL}`が見つかりませんでした。", color=0xFF0000))
                asyncio.ensure_future(self.collection.update_one({"guild_id": ctx.guild.id}, {"$set": InviteData}))

        else:
            await ctx.reply(embed=nextcord.Embed(title="エラー", description="引数が不正です。", color=0xFF0000))

    @commands.bot_has_permissions(manage_guild=True)
    @commands.Cog.listener()
    async def on_invite_create(self, invite: nextcord.Invite):
        asyncio.ensure_future(self.fetch_invite(await invite.guild.invites(), invite.guild.id))


    @commands.bot_has_permissions(manage_guild=True)
    @commands.Cog.listener()
    async def on_invite_delete(self, invite: nextcord.Invite):
        await self.fetch_invite(await invite.guild.invites(), invite.guild.id)
        InviteData = await self.collection.find_one({"guild_id": invite.guild.id})
        if invite.url in InviteData:
            del InviteData[invite.url]
        asyncio.ensure_future(self.collection.update_one({"guild_id": Interaction.guild.id}, {"$set": InviteData}))


def setup(bot, **kwargs):
    bot.add_cog(Invite(bot, **kwargs))
