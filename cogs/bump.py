from nextcord.ext import commands
from nextcord import Interaction, SlashOption
import nextcord
import datetime
import pickle
import re
import random
import asyncio
import time
import math

import sys
from util import admin_check, n_fc, eh, slash_tool
import util.srtr as srtr

#Bump通知

SET, DEL, STATUS = [0,1,2]


class bump(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def bump_config(
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
            if interaction.guild.id not in n_fc.bump_list:
                return slash_tool.messages.mreply(embed=nextcord.Embed(title="Bump通知", description=f"{interaction.guild.name}でBump設定は無効です。", color=0x00ff00))
            else:
                if n_fc.bump_list[interaction.guild.id] != None:
                    return slash_tool.messages.mreply(embed=nextcord.Embed(title="Bump通知", description=f"{interaction.guild.name}でBump設定は有効です。\nメンションロール:<@&{n_fc.bump_list[interaction.guild.id]}>", color=0x00ff00))
                else:
                    return slash_tool.messages.mreply(embed=nextcord.Embed(title="Bump通知", description=f"{interaction.guild.name}でBump設定は有効です。\nメンションロール:なし", color=0x00ff00))
        elif action == SET:
            if admin_check.admin_check(interaction.guild, user):
                n_fc.bump_list[interaction.guild.id] = item
                if n_fc.bump_list[interaction.guild.id] != None:
                    return slash_tool.messages.mreply(embed=nextcord.Embed(title="Bump通知", description=f"{interaction.guild.name}でBump通知の設定を有効にしました。\nメンションロール:<@&{n_fc.bump_list[interaction.guild.id]}>", color=0x00ff00))
                else:
                    return slash_tool.messages.mreply(embed=nextcord.Embed(title="Bump通知", description=f"{interaction.guild.name}でBump通知の設定を有効にしました。\nメンションロール:なし", color=0x00ff00))
            else:
                return slash_tool.messages.mreply(embed=nextcord.Embed(title="エラー", description=f"管理者権限がありません。", color=0xff0000))
        elif action == DEL:
            if admin_check.admin_check(interaction.guild, user):
                del n_fc.bump_list[interaction.guild.id]
                return slash_tool.messages.mreply(embed=nextcord.Embed(title="Bump通知", description=f"{interaction.guild.name}でBump通知の設定を無効にしました。", color=0x00ff00))
            else:
                return slash_tool.messages.mreply(embed=nextcord.Embed(title="エラー", description=f"管理者権限がありません。", color=0xff0000))
        else:
            return slash_tool.messages.mreply(embed=nextcord.Embed(title="Bump設定", description="`n!bump`:Bump通知の設定の状態表示\n`n!bump on`:サーバーでのBump通知の設定を有効にします。\n`n!bump off`:サーバーでのBump通知の設定を無効にします。", color=0x00ff00))
    
    @commands.command(name="bump", help="""\
Disboardの通知設定を行います。

・使い方
`n!bump [on/off] [*ロール]`
**on**の場合、ロールを後ろにつけると、ロールをメンションします。

・例
`n!bump on`
`n!bump on @Bumper`
`n!bump off`
""")
    async def bump(self, ctx: commands.Context):
        args = ctx.message.content.split(" ",3)
        if len(args) == 1:
            await self.bump_config(ctx, STATUS, None)
        elif args[1] == "on":
            if len(args) == 2:
                await self.bump_config(ctx, SET, None)
            else:
                role = None
                try:
                    role = ctx.guild.get_roles(int(args[2]))
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
            await self.bump_config(ctx, 302050872383242240, None)
    
    @nextcord.slash_command(name="bump", description="bumpの設定をします")
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
        if message.guild.id not in n_fc.bump_list:
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
            bump_rnd = random.randint(1,3)
            messageContent = ""
            if n_fc.bump_list[message.guild.id] is None:
                messageContent = "にらBOT Bump通知"
            else:
                messageContent = f"<@&{n_fc.bump_list[message.guild.id]}>"
            if bump_rnd == 1:
                await message.channel.send(messageContent, embed=nextcord.Embed(title="Bumpの時間よ！", description=f"Bumpしたければすればいいんじゃないの...？(ツンデレ)\n```/bump```", color=0x00ff00))
            elif bump_rnd == 2:
                await message.channel.send(messageContent, embed=nextcord.Embed(title="Bumpしやがれください！", description=f"お前がBumpするんだよ、あくしろよ！\n```/bump```", color=0x00ff00))
            elif bump_rnd == 3:
                await message.channel.send(messageContent, embed=nextcord.Embed(title="Bumpしましょう！", description=f"Bumpの時間ですよ！\n```/bump```", color=0x00ff00))
            return

def setup(bot):
    bot.add_cog(bump(bot))
