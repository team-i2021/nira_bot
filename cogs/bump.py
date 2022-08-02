import asyncio
import datetime
import math
import pickle
import random
import re
import sys
import time

import HTTP_db
import nextcord
from nextcord import Interaction, SlashOption
from nextcord.ext import commands

import util.srtr as srtr
from util import admin_check, n_fc, eh, slash_tool, database

# Bump通知

SET, DEL, STATUS = [0, 1, 2]

class bump_data:
    name = "bump_data"
    value = {}
    default = {}
    value_type = database.GUILD_VALUE

class Bump(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.client = database.openClient()
        asyncio.ensure_future(database.default_pull(self.client, bump_data))

    async def bump_config(
        self,
        interaction: Interaction or commands.Context,
        action: int,
        item
    ):
        user = None
        if type(interaction) == Interaction:
            user = interaction.user
        else:
            user = interaction.author
        if action == STATUS:
            if interaction.guild.id not in bump_data.value:
                await slash_tool.messages.mreply(interaction, "", embed=nextcord.Embed(title="Bump通知", description=f"{interaction.guild.name}でBump設定は無効です。", color=0x00ff00), ephemeral=True)
            else:
                if bump_data.value[interaction.guild.id] != None:
                    await slash_tool.messages.mreply(interaction, "", embed=nextcord.Embed(title="Bump通知", description=f"{interaction.guild.name}でBump設定は有効です。\nメンションロール:<@&{bump_data.value[interaction.guild.id]}>", color=0x00ff00), ephemeral=True)
                else:
                    await slash_tool.messages.mreply(interaction, "", embed=nextcord.Embed(title="Bump通知", description=f"{interaction.guild.name}でBump設定は有効です。\nメンションロール:なし", color=0x00ff00), ephemeral=True)
        elif action == SET:
            if admin_check.admin_check(interaction.guild, user):
                if item is None:
                    bump_data.value[interaction.guild.id] = None
                else:
                    bump_data.value[interaction.guild.id] = item.id
                await database.default_push(self.client, bump_data)
                if bump_data.value[interaction.guild.id] is not None:
                    await slash_tool.messages.mreply(interaction, "", embed=nextcord.Embed(title="Bump通知", description=f"{interaction.guild.name}でBump通知の設定を有効にしました。\nメンションロール:<@&{bump_data.value[interaction.guild.id]}>", color=0x00ff00), ephemeral=True)
                else:
                    await slash_tool.messages.mreply(interaction, "", embed=nextcord.Embed(title="Bump通知", description=f"{interaction.guild.name}でBump通知の設定を有効にしました。\nメンションロール:なし", color=0x00ff00), ephemeral=True)
            else:
                await slash_tool.messages.mreply(interaction, "", embed=nextcord.Embed(title="エラー", description=f"管理者権限がありません。", color=0xff0000), ephemeral=True)
        elif action == DEL:
            if admin_check.admin_check(interaction.guild, user):
                del bump_data.value[interaction.guild.id]
                await database.default_push(self.client, bump_data)
                await slash_tool.messages.mreply(interaction, "", embed=nextcord.Embed(title="Bump通知", description=f"{interaction.guild.name}でBump通知の設定を無効にしました。", color=0x00ff00), ephemeral=True)
            else:
                await slash_tool.messages.mreply(interaction, "", embed=nextcord.Embed(title="エラー", description=f"管理者権限がありません。", color=0xff0000), ephemeral=True)
        else:
            await slash_tool.messages.mreply(interaction, "", embed=nextcord.Embed(title="Bump設定", description=f"`n!bump`:Bump通知の設定の状態表示\n`n!bump on`:サーバーでのBump通知の設定を有効にします。\n`{self.bot.command_prefix}bump off`:サーバーでのBump通知の設定を無効にします。", color=0x00ff00), ephemeral=True)

    @commands.command(name="bump", help="""\
Disboardの通知設定を行います。

・使い方
`n!bump [on/off] [*ロール]`
**on**の場合、ロールを後ろにつけると、ロールをメンションします。

・例
`n!bump on`
`n!bump on @Bumper`
`n!bump off`""")
    async def bump(self, ctx: commands.Context):
        args = ctx.message.content.split(" ", 3)
        if len(args) == 1:
            await self.bump_config(ctx, STATUS, None)
        elif args[1] == "on":
            if len(args) == 2:
                await self.bump_config(ctx, SET, None)
            else:
                role = None
                try:
                    role = ctx.guild.get_role(int(args[2]))
                except ValueError:
                    pass

                if role is None:
                    for i in ctx.guild.roles:
                        if i.name == args[2]:
                            role = i
                            break

                if role is None:
                    await ctx.reply(embed=nextcord.Embed(title="エラー", description=f"指定したロール`{args[2]}`が見つかりませんでした。", color=0xff0000))
                    return

                await self.bump_config(ctx, SET, role)
        elif args[1] == "off":
            await self.bump_config(ctx, DEL, None)
        else:
            await self.bump_config(ctx, -1, None)

    @nextcord.slash_command(name="bump", description="bumpの設定をします", guild_ids=n_fc.GUILD_IDS)
    async def bump_slash(self, interaction):
        pass

    @bump_slash.subcommand(name="set", description="bumpの通知をします")
    async def set_slash(
        self,
        interaction: Interaction,
        role: nextcord.Role = SlashOption(
            name="role",
            description="bump通知をする際にメンションしてほしい場合は指定します",
            required=False
        )
    ):
        await self.bump_config(interaction, SET, role)
        return

    @bump_slash.subcommand(name="del", description="bumpの通知設定を削除します")
    async def del_slash(
        self,
        interaction: Interaction
    ):
        await self.bump_config(interaction, DEL, None)
        return

    @bump_slash.subcommand(name="status", description="bump通知の設定状況を確認します")
    async def status_slash(
        self,
        interaction: Interaction
    ):
        await self.bump_config(interaction, STATUS, None)
        return

    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message):
        if message.guild == None:
            return
        if message.guild.id not in bump_data.value:
            return
        if message.author.id != 302050872383242240:
            return
        if message.embeds == []:
            return
        if message.embeds[0].title != "DISBOARD: The Public Server List" and message.embeds[0].title != "DISBOARD: Discordサーバー掲示板":
            return
        if re.search("Bump done!", message.embeds[0].description) or re.search("表示順をアップしたよ", message.embeds[0].description):
            print("bump set.")
            await message.channel.send(embed=nextcord.Embed(title="Bump通知設定", description=f"<t:{math.floor(time.time())+7200}:f>、<t:{math.floor(time.time())+7200}:R>に通知します。", color=0x00ff00))
            await asyncio.sleep(7200)
            bump_rnd = random.randint(1, 3)
            messageContent = ""
            if bump_data.value[message.guild.id] is None:
                messageContent = "にらBOT Bump通知"
            else:
                messageContent = f"<@&{bump_data.value[message.guild.id]}>"
            if bump_rnd == 1:
                await message.channel.send(messageContent, embed=nextcord.Embed(title="Bumpの時間よ！", description=f"Bumpしたければすればいいんじゃないの...？(ツンデレ)\n```/bump```", color=0x00ff00))
            elif bump_rnd == 2:
                await message.channel.send(messageContent, embed=nextcord.Embed(title="Bumpしやがれください！", description=f"お前がBumpするんだよ、あくしろよ！\n```/bump```", color=0x00ff00))
            elif bump_rnd == 3:
                await message.channel.send(messageContent, embed=nextcord.Embed(title="Bumpしましょう！", description=f"Bumpの時間ですよ！\n```/bump```", color=0x00ff00))
            return


def setup(bot):
    bot.add_cog(Bump(bot))
