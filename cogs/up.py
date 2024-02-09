import asyncio
import logging
import math
import random
import time
from re import compile

import nextcord
from nextcord import Interaction, SlashOption
from nextcord.ext import commands, tasks, application_checks

from motor import motor_asyncio

from util.n_fc import GUILD_IDS
from util import slash_tool
from util.nira import NIRA

SET, DEL, STATUS = (0, 1, 2)
ROLE_ID = compile(r"<@&[0-9]+?>")


async def UpNotifyConfig(collection: motor_asyncio.AsyncIOMotorCollection, interaction, config_type: int, value: int or None):
    upper = await collection.find_one({"guild_id": interaction.guild.id})

    if config_type == STATUS:
        if upper is None:
            await slash_tool.messages.mreply(interaction, "", embed=nextcord.Embed(title="Up通知", description=f"この`{interaction.guild.name}`にはUp通知が設定されていません。", color=0x00ff00))
        else:
            if upper["role_id"] is None:
                await slash_tool.messages.mreply(interaction, "", embed=nextcord.Embed(title="Up通知", description=f"この`{interaction.guild.name}`にはUp通知が設定されています。\nメンションロール: なし", color=0x00ff00))
            else:
                await slash_tool.messages.mreply(interaction, "", embed=nextcord.Embed(title="Up通知", description=f"この`{interaction.guild.name}`にはUp通知が設定されています。\nメンションロール: <@&{upper['role_id']}>", color=0x00ff00))

    elif config_type == SET:
        upper["role_id"] = value
        asyncio.ensure_future(collection.update_one({"guild_id": interaction.guild.id}, {"$set": upper}, upsert=True))

        if upper["role_id"] is None:
            await slash_tool.messages.mreply(interaction, "", embed=nextcord.Embed(title="Up通知", description=f"この`{interaction.guild.name}`にはUp通知が設定されています。\nメンションロール: なし", color=0x00ff00))
        else:
            await slash_tool.messages.mreply(interaction, "", embed=nextcord.Embed(title="Up通知", description=f"この`{interaction.guild.name}`にはUp通知が設定されています。\nメンションロール: <@&{upper['role_id']}>", color=0x00ff00))

    elif config_type == DEL:
        if upper is None:
            await slash_tool.messages.mreply(interaction, "", embed=nextcord.Embed(title="Up通知", description=f"この`{interaction.guild.name}`にはUp通知が設定されていません。", color=0xff0000))
        else:
            await collection.delete_one({"guild_id": interaction.guild.id})
            await slash_tool.messages.mreply(interaction, "", embed=nextcord.Embed(title="Up通知", description=f"この`{interaction.guild.name}`でのUp通知設定を解除しました。", color=0x00ff00))


async def ErrorSend(ctx: commands.Context):
    await slash_tool.messages.mreply(ctx, "", embed=nextcord.Embed(title="エラー", description=f"コマンドの引数が異なります。\n`{ctx.prefix}up [on/off] [*メンションするロール]`", color=0xff0000))


class UpNotify(commands.Cog):
    def __init__(self, bot: NIRA):
        self.bot = bot
        self.collection = self.bot.database["up_notify"]

    @commands.has_permissions(manage_guild=True)
    @commands.command(name="up", aliases=["アップ", "あっぷ", "dissoku"], help="""\
DissokuのUp通知を行います

もうそのまんまです。
DissokuのUpをしたら、その1時間後に通知します。


・使い方
`n!up [on/off] [*ロール]`
**on**の場合、ロールを後ろにつけると、通知時にロールをメンションします。

・例
`n!up on`
`n!up on @( ᐛ )وｱｯﾊﾟｧｧｧｧｧｧｧｧｧｧｧｧｧｧ!!`
`n!up off`""")
    async def up(self, ctx: commands.Context):
        args = ctx.message.content.split(" ", 3)
        if len(args) == 1:
            await UpNotifyConfig(self.collection, ctx, STATUS, None)
        elif len(args) > 3:
            await ErrorSend(ctx)
        elif len(args) == 2:
            if args[1] == "on":
                await UpNotifyConfig(self.collection, ctx, SET, None)
            elif args[1] == "off":
                await UpNotifyConfig(self.collection, ctx, DEL, None)
            else:
                await ErrorSend(ctx)
        else:
            if args[1] == "on":
                if ROLE_ID.fullmatch(args[2]):
                    await UpNotifyConfig(
                        self.collection,
                        ctx,
                        SET,
                        int(ROLE_ID.fullmatch(args[2]).group().replace("<@&", "").replace(">", ""))
                    )
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

                await UpNotifyConfig(self.collection, ctx, SET, role.id)
            else:
                await ErrorSend(ctx)

    @application_checks.has_permissions(manage_guild=True)
    @nextcord.slash_command(name="up", description="Dissoku notification")
    async def up_slash(self, interaction: Interaction):
        pass

    @application_checks.has_permissions(manage_guild=True)
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
        if role is not None:
            role = role.id
        await UpNotifyConfig(self.collection, interaction, SET, role)

    @application_checks.has_permissions(manage_guild=True)
    @up_slash.subcommand(name="off", description="Turn OFF notification of Dissoku", description_localizations={nextcord.Locale.ja: "Dissoku通知を無効にします"})
    async def up_slash_off(self, interaction: Interaction):
        await UpNotifyConfig(self.collection, interaction, DEL, None)

    @application_checks.has_permissions(manage_guild=True)
    @up_slash.subcommand(name="status", description="Status of notification of Dissoku", description_localizations={nextcord.Locale.ja: "Dissoku通知の状態を確認します"})
    async def up_slash_status(self, interaction: Interaction):
        await UpNotifyConfig(self.collection, interaction, STATUS, None)


    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message):
        if isinstance(message.channel, nextcord.DMChannel):
            return
        result = await self.collection.find_one({"guild_id": message.guild.id})
        if result is None:
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
                    if result["role_id"] is None:
                        messageContent = "にらBOT Up通知"
                    else:
                        messageContent = f"<@&{result['role_id']}>"
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


def setup(bot):
    bot.add_cog(UpNotify(bot))
