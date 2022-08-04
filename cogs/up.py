import asyncio
import json
import logging
import math
import os
import random
import re
import sys
import time
from re import compile

import gspread
import nextcord
from nextcord import Interaction, SlashOption
from nextcord.ext import commands, tasks

from util.n_fc import GUILD_IDS, py_admin
from util import slash_tool, admin_check, database

SET, DEL, STATUS = (0, 1, 2)
ROLE_ID = compile(r"<@&[0-9]+?>")

DBS = database.openSheet()
DATABASE_KEY = "B4"

UpperData = {}


def readDatabase() -> None:
    if DBS.acell(DATABASE_KEY).value != "" and DBS.acell(DATABASE_KEY).value is not None:
        global UpperData
        UpperData = json.loads(DBS.acell(DATABASE_KEY).value)
        UpperDataTemp = {}
        for key, value in UpperData.items():
            UpperDataTemp[int(key)] = value
        UpperData = UpperDataTemp
    return


def writeDatabase() -> None:
    DBS.update_acell(DATABASE_KEY, json.dumps(UpperData))
    return


def UpNotifyConfig(bot: commands.Bot, interaction, config_type: int, value: int or None):
    if config_type == STATUS:
        if interaction.guild.id not in UpperData:
            return slash_tool.messages.mreply(interaction, "", embed=nextcord.Embed(title="Up通知", description=f"この`{interaction.guild.name}`にはUp通知が設定されていません。", color=0x00ff00))
        else:
            if UpperData[interaction.guild.id] is None:
                return slash_tool.messages.mreply(interaction, "", embed=nextcord.Embed(title="Up通知", description=f"この`{interaction.guild.name}`にはUp通知が設定されています。\nメンションロール: なし", color=0x00ff00))
            else:
                return slash_tool.messages.mreply(interaction, "", embed=nextcord.Embed(title="Up通知", description=f"この`{interaction.guild.name}`にはUp通知が設定されています。\nメンションロール: <@&{UpperData[interaction.guild.id]}>", color=0x00ff00))
    elif config_type == SET:
        UpperData[interaction.guild.id] = value
        writeDatabase()
        if UpperData[interaction.guild.id] is None:
            return slash_tool.messages.mreply(interaction, "", embed=nextcord.Embed(title="Up通知", description=f"この`{interaction.guild.name}`にはUp通知が設定されています。\nメンションロール: なし", color=0x00ff00))
        else:
            return slash_tool.messages.mreply(interaction, "", embed=nextcord.Embed(title="Up通知", description=f"この`{interaction.guild.name}`にはUp通知が設定されています。\nメンションロール: <@&{UpperData[interaction.guild.id]}>", color=0x00ff00))
    elif config_type == DEL:
        if interaction.guild.id not in UpperData:
            return slash_tool.messages.mreply(interaction, "", embed=nextcord.Embed(title="Up通知", description=f"この`{interaction.guild.name}`にはUp通知が設定されていません。", color=0xff0000))
        else:
            del UpperData[interaction.guild.id]
            writeDatabase()
            return slash_tool.messages.mreply(interaction, "", embed=nextcord.Embed(title="Up通知", description=f"この`{interaction.guild.name}`でのUp通知設定を解除しました。", color=0x00ff00))


async def ErrorSend(interaction):
    return slash_tool.messages.mreply(interaction, "", embed=nextcord.Embed(title="エラー", description=f"コマンドの引数が異なります。\n`n!up [on/off] [*メンションするロール]`", color=0xff0000))


class UpNotify(commands.Cog):
    def __init__(self, bot: commands.Bot, **kwargs):
        self.bot = bot
        self.client = kwargs["client"]

    @commands.command(name="up", aliases=["アップ", "あっぷ", "dissoku"], help="""\
DissokuのUp通知を行います

もうそのまんまです。
DissokuのUpをしたら、その1時間後に通知します。


・使い方
`n!up [on/off] [*ロール]`
**on**の場合、ロールを後ろにつけると、ロールをメンションします。

・例
`n!up on`
`n!up on @( ᐛ )وｱｯﾊﾟｧｧｧｧｧｧｧｧｧｧｧｧｧｧ!!`
`n!up off`""")
    async def up(self, ctx: commands.Context):
        if admin_check.admin_check(ctx.guild, ctx.author):
            args = ctx.message.content.split(" ", 3)
            if len(args) == 1:
                await UpNotifyConfig(self.bot, ctx, STATUS, None)
                return
            elif len(args) > 3:
                await ErrorSend(ctx)
                # error
                return
            elif len(args) == 2:
                if args[1] == "on":
                    await UpNotifyConfig(self.bot, ctx, SET, None)
                elif args[1] == "off":
                    await UpNotifyConfig(self.bot, ctx, DEL, None)
                elif args[1][:5] == "debug":
                    if ctx.author.id in py_admin:
                        debugArg = args[1].split(":", 1)
                        if len(debugArg) == 1:
                            debugArg = ""
                        else:
                            debugArg = debugArg[1]
                        if debugArg == "current":
                            await ctx.reply(f"```py\n[SHOW] Device\n{UpperData}```")
                        elif debugArg == "server":
                            await ctx.reply(f"```py\n[SHOW] Server\n{DBS.acell(DATABASE_KEY).value}```")
                        elif debugArg == "write":
                            writeDatabase()
                            await ctx.reply(f"```sh\n[WRITE] Device -> Server\nExecuted.```")
                        elif debugArg == "read":
                            readDatabase()
                            await ctx.reply(f"```sh\n[READ] Server -> Device\nExecuted.```")
                        else:
                            await ctx.reply(f"""\
```sh
[HELP] Database Manager

n!up debug:[command]

current - Show UpperData of device
server - Show UpperData of server
write - write UpperData of device to server
read - read UpperData from server to device```""")
                        return
                    else:
                        await ctx.reply(embed=nextcord.Embed(title="エラー", description="あなたはBOTの管理者ではありません。", color=0xff0000))
                        return
                else:
                    await ErrorSend(ctx)
                return
            else:
                if args[1] == "on":
                    if ROLE_ID.fullmatch(args[2]):
                        await UpNotifyConfig(self.bot, ctx, SET, int(ROLE_ID.fullmatch(args[2]).group().replace("<@&", "").replace(">", "")))
                        return

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
                    await UpNotifyConfig(self.bot, ctx, SET, role.id)
                    return
                else:
                    await ErrorSend(ctx)
        else:
            await ctx.reply(embed=nextcord.Embed(title="エラー", description="管理者権限がありません。", color=0xff0000))
            return

    @nextcord.slash_command(name="up", description="Dissoku通知", guild_ids=GUILD_IDS)
    async def up_slash(self, interaction: Interaction):
        pass

    @up_slash.subcommand(name="on", description="Dissoku通知を有効にします")
    async def up_slash_on(
        self,
        interaction: Interaction,
        role: nextcord.Role = SlashOption(
            name="role",
            description="メンションするロールです",
            required=False
        )
    ):
        if admin_check.admin_check(interaction.guild, interaction.user):
            if not role is None:
                role = role.id
            await UpNotifyConfig(self.bot, interaction, SET, role)
        else:
            await interaction.reply(embed=nextcord.Embed(title="エラー", description="管理者権限がありません。", color=0xff0000))

    @up_slash.subcommand(name="off", description="Dissoku通知を無効にします")
    async def up_slash_off(self, interaction: Interaction):
        if admin_check.admin_check(interaction.guild, interaction.user):
            await UpNotifyConfig(self.bot, interaction, DEL, None)
        else:
            await interaction.reply(embed=nextcord.Embed(title="エラー", description="管理者権限がありません。", color=0xff0000))

    @up_slash.subcommand(name="status", description="Dissoku通知の状態を確認します")
    async def up_slash_status(self, interaction: Interaction):
        await UpNotifyConfig(self.bot, interaction, STATUS, None)

    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message):
        await asyncio.sleep(5)
        if message.guild == None:
            return
        if message.guild.id not in UpperData:
            return
        if message.author.id != 761562078095867916:
            return
        if message.embeds == []:
            return
        if message.embeds[0].title != "ディスコード速報 | Discordサーバー・友達募集・ボット掲示板":
            return
        if message.embeds[0].fields[0].name == f"`{message.guild.name}` をアップしたよ!":
            try:
                print("up set.")
                await message.channel.send(embed=nextcord.Embed(title="Up通知設定", description=f"<t:{math.floor(time.time())+3600}:f>、<t:{math.floor(time.time())+3600}:R>に通知します。", color=0x00ff00))
                await asyncio.sleep(3600)
                up_rnd = random.randint(1, 3)
                messageContent = ""
                if UpperData[message.guild.id] is None:
                    messageContent = "にらBOT Up通知"
                else:
                    messageContent = f"<@&{UpperData[message.guild.id]}>"
                if up_rnd == 1:
                    await message.channel.send(messageContent, embed=nextcord.Embed(title="Upの時間だけどぉ！？！？", description=f"ほらほら～Upしないのぉ？？？\n```/dissoku up```", color=0x00ff00))
                elif up_rnd == 2:
                    await message.channel.send(messageContent, embed=nextcord.Embed(title="Upしやがれください！", description=f"お前がUpするんだよ、あくしろよ！\n```/dissoku up```", color=0x00ff00))
                elif up_rnd == 3:
                    await message.channel.send(messageContent, embed=nextcord.Embed(title="Upしましょう！", description=f"Upしてみませんか！\n```/dissoku up```", color=0x00ff00))
                return
            except Exception as err:
                logging.error(err)

    @tasks.loop(seconds=30)
    async def writeDatabaseLoop(self):
        writeDatabase()
        return


def setup(bot, **kwargs):
    readDatabase()
    bot.add_cog(UpNotify(bot, **kwargs))
    UpNotify.writeDatabaseLoop.start(UpNotify(bot))


def teardown(bot):
    UpNotify.writeDatabaseLoop.cancel()
    writeDatabase()
