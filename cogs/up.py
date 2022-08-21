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

import HTTP_db
import nextcord
from nextcord import Interaction, SlashOption
from nextcord.ext import commands, tasks

from util.n_fc import GUILD_IDS
from util import slash_tool, admin_check, database
from util.nira import NIRA

SET, DEL, STATUS = (0, 1, 2)
ROLE_ID = compile(r"<@&[0-9]+?>")


class Upper:
    name = "dissoku_data"
    value = {}
    default = {}
    value_type = database.GUILD_VALUE


async def UpNotifyConfig(bot: commands.Bot, client: HTTP_db.Client, interaction, config_type: int, value: int or None):
    if config_type == STATUS:
        if interaction.guild.id not in Upper.value:
            return slash_tool.messages.mreply(interaction, "", embed=nextcord.Embed(title="Up通知", description=f"この`{interaction.guild.name}`にはUp通知が設定されていません。", color=0x00ff00))
        else:
            if Upper.value[interaction.guild.id] is None:
                return slash_tool.messages.mreply(interaction, "", embed=nextcord.Embed(title="Up通知", description=f"この`{interaction.guild.name}`にはUp通知が設定されています。\nメンションロール: なし", color=0x00ff00))
            else:
                return slash_tool.messages.mreply(interaction, "", embed=nextcord.Embed(title="Up通知", description=f"この`{interaction.guild.name}`にはUp通知が設定されています。\nメンションロール: <@&{Upper.value[interaction.guild.id]}>", color=0x00ff00))
    elif config_type == SET:
        Upper.value[interaction.guild.id] = value
        await database.default_push(client, Upper)
        if Upper.value[interaction.guild.id] is None:
            return slash_tool.messages.mreply(interaction, "", embed=nextcord.Embed(title="Up通知", description=f"この`{interaction.guild.name}`にはUp通知が設定されています。\nメンションロール: なし", color=0x00ff00))
        else:
            return slash_tool.messages.mreply(interaction, "", embed=nextcord.Embed(title="Up通知", description=f"この`{interaction.guild.name}`にはUp通知が設定されています。\nメンションロール: <@&{Upper.value[interaction.guild.id]}>", color=0x00ff00))
    elif config_type == DEL:
        if interaction.guild.id not in Upper.value:
            return slash_tool.messages.mreply(interaction, "", embed=nextcord.Embed(title="Up通知", description=f"この`{interaction.guild.name}`にはUp通知が設定されていません。", color=0xff0000))
        else:
            del Upper.value[interaction.guild.id]
            await database.default_push(client, Upper)
            return slash_tool.messages.mreply(interaction, "", embed=nextcord.Embed(title="Up通知", description=f"この`{interaction.guild.name}`でのUp通知設定を解除しました。", color=0x00ff00))


async def ErrorSend(interaction):
    return slash_tool.messages.mreply(interaction, "", embed=nextcord.Embed(title="エラー", description=f"コマンドの引数が異なります。\n`{self.bot.command_prefix}up [on/off] [*メンションするロール]`", color=0xff0000))


class UpNotify(commands.Cog):
    def __init__(self, bot: NIRA, **kwargs):
        self.bot = bot
        asyncio.ensure_future(database.default_pull(self.bot.client, Upper))

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
                await (await UpNotifyConfig(self.bot, self.bot.client, ctx, STATUS, None))
                return
            elif len(args) > 3:
                await ErrorSend(ctx)
                # error
                return
            elif len(args) == 2:
                if args[1] == "on":
                    await (await UpNotifyConfig(self.bot, self.bot.client, ctx, SET, None))
                elif args[1] == "off":
                    await (await UpNotifyConfig(self.bot, self.bot.client, ctx, DEL, None))
                elif args[1][:5] == "debug":
                    if await self.bot.is_owner(ctx.author):
                        debugArg = args[1].split(":", 1)
                        if len(debugArg) == 1:
                            debugArg = ""
                        else:
                            debugArg = debugArg[1]
                        if debugArg == "current":
                            await ctx.reply(f"```py\n# [SHOW] Device\n{Upper.value}```")
                        elif debugArg == "write":
                            await database.default_push(self.bot.client, Upper)
                            await ctx.reply(f"```sh\n[WRITE] Device -> Server\nExecuted.```")
                        elif debugArg == "read":
                            await database.default_pull(self.bot.client, Upper)
                            await ctx.reply(f"```sh\n[READ] Server -> Device\nExecuted.```")
                        else:
                            await ctx.reply(f"""\
```sh
[HELP] Database Manager

n!up debug:[command]

current - Show Upper.value of device
write - write Upper.value of device to server
read - read Upper.value from server to device```""")
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
                        await (await UpNotifyConfig(self.bot, self.bot.client, ctx, SET, int(ROLE_ID.fullmatch(args[2]).group().replace("<@&", "").replace(">", ""))))
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
                    await (await UpNotifyConfig(self.bot, self.bot.client, ctx, SET, role.id))
                    return
                else:
                    await ErrorSend(ctx)
        else:
            await ctx.reply(embed=nextcord.Embed(title="エラー", description="管理者権限がありません。", color=0xff0000))
            return

    @nextcord.slash_command(name="up", description="Dissoku notification", guild_ids=GUILD_IDS)
    async def up_slash(self, interaction: Interaction):
        pass

    @up_slash.subcommand(name="on", description="Turn ON notification of Dissoku", description_localizations={nextcord.Locale.ja: "Dissoku通知を有効にします"})
    async def up_slash_on(
        self,
        interaction: Interaction,
        role: nextcord.Role = SlashOption(
            name="role",
            description="Role of mention",
            description_localizations={nextcord.Locale.ja: "メンションするロールです"},
            required=False
        )
    ):
        if admin_check.admin_check(interaction.guild, interaction.user):
            if role is not None:
                role = role.id
            await (await UpNotifyConfig(self.bot, self.bot.client, interaction, SET, role))
        else:
            await interaction.reply(embed=nextcord.Embed(title="エラー", description="管理者権限がありません。", color=0xff0000))

    @up_slash.subcommand(name="off", description="Turn OFF notification of Dissoku", description_localizations={nextcord.Locale.ja: "Dissoku通知を無効にします"})
    async def up_slash_off(self, interaction: Interaction):
        if admin_check.admin_check(interaction.guild, interaction.user):
            await (await UpNotifyConfig(self.bot, self.bot.client, interaction, DEL, None))
        else:
            await interaction.reply(embed=nextcord.Embed(title="エラー", description="管理者権限がありません。", color=0xff0000))

    @up_slash.subcommand(name="status", description="Status of notification of Dissoku", description_localizations={nextcord.Locale.ja: "Dissoku通知の状態を確認します"})
    async def up_slash_status(self, interaction: Interaction):
        await (await UpNotifyConfig(self.bot, self.bot.client, interaction, STATUS, None))

    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message):
        if isinstance(message.channel, nextcord.DMChannel):
            return
        if message.guild.id not in Upper.value:
            return
        if message.author.id != 761562078095867916:
            return
        for _ in range(20):
            message = await message.channel.fetch_message(message.id)
            if message.embeds == []:
                await asyncio.sleep(0.5)
                continue
            if message.embeds[0].title != "ディスコード速報 | Discordサーバー・友達募集・ボット掲示板":
                await asyncio.sleep(0.5)
                continue
            if message.embeds[0].fields[0].name == f"`{message.guild.name}` をアップしたよ!":
                try:
                    print("up set.")
                    await message.channel.send(embed=nextcord.Embed(title="Up通知設定", description=f"<t:{math.floor(time.time())+3600}:f>、<t:{math.floor(time.time())+3600}:R>に通知します。", color=0x00ff00))
                    await asyncio.sleep(3600)
                    up_rnd = random.randint(1, 3)
                    messageContent = ""
                    if Upper.value[message.guild.id] is None:
                        messageContent = "にらBOT Up通知"
                    else:
                        messageContent = f"<@&{Upper.value[message.guild.id]}>"
                    if up_rnd == 1:
                        await message.channel.send(messageContent, embed=nextcord.Embed(title="Upの時間だけどぉ！？！？", description=f"ほらほら～Upしないのぉ？？？\n```/dissoku up```", color=0x00ff00))
                    elif up_rnd == 2:
                        await message.channel.send(messageContent, embed=nextcord.Embed(title="Upしやがれください！", description=f"お前がUpするんだよ、あくしろよ！\n```/dissoku up```", color=0x00ff00))
                    elif up_rnd == 3:
                        await message.channel.send(messageContent, embed=nextcord.Embed(title="Upしましょう！", description=f"Upしてみませんか！\n```/dissoku up```", color=0x00ff00))
                    return
                except Exception as err:
                    logging.error(err)
                    return
            else:
                return


def setup(bot, **kwargs):
    bot.add_cog(UpNotify(bot, **kwargs))
