import asyncio
import datetime
import json
import logging
import os
import sys
import traceback
from re import compile

import nextcord
from nextcord import Interaction, SlashOption, ChannelType
from nextcord.ext import commands, tasks
from motor import motor_asyncio

from util import admin_check, n_fc, eh, database, dict_list
from util.nira import NIRA

# りまいんど

TIME_CHECK = compile(r"[0-9]{1,2}:[0-9]{1,2}")


class RemindMaker(nextcord.ui.Modal):
    def __init__(self, collection):
        super().__init__(
            "リマインドメッセージ設定",
            timeout=None,
        )

        self.remind_time = nextcord.ui.TextInput(
            label="メッセージを送信する時間",
            style=nextcord.TextInputStyle.short,
            placeholder="3:34",
            min_length=3,
            max_length=5,
            required=True,
        )
        self.add_item(self.remind_time)

        self.remind_content = nextcord.ui.TextInput(
            label="送信するメッセージ内容",
            style=nextcord.TextInputStyle.paragraph,
            placeholder="おきてー！朝（深夜）なのだー！僕の朝食（夜食）を作るのだ！ちなみに今日は%date%なのだ！",
            required=True,
        )
        self.add_item(self.remind_content)
        self.collection = collection

    async def callback(self, interaction: nextcord.Interaction) -> None:
        await interaction.response.defer()

        if len(self.remind_time.value) > 5 or len(self.remind_time.value) < 3:
            await interaction.followup.send("・エラー\n時間の入力が不正です。\n`/remind on`", ephemeral=True)
            return

        time = TIME_CHECK.fullmatch(self.remind_time.value)
        if time is None:
            await interaction.followup.send("・エラー\n時間の入力が不正です。\n`/remind on`", ephemeral=True)
            return

        time = time.group()
        if int(time.split(":")[0]) > 23 or int(time.split(":")[1]) > 59:
            await interaction.followup.send("・エラー\n時間の入力が不正です。\n`/remind on`", ephemeral=True)
            return

        time = ":".join([f"0{i}"[-2:] for i in time.split(":", 1)])
        
        await self.collection.update_one({"channel_id": interaction.channel.id}, {"$set": {"message": self.remind_content.value, "time": time}}, upsert=True)
        await interaction.followup.send(embed=nextcord.Embed(title="設定完了", description=f"毎日`{time}`に <#{interaction.channel.id}> にリマインドメッセージを送信します。", color=0x00ff00))
        return


class Remind(commands.Cog):
    def __init__(self, bot: NIRA, **kwargs):
        self.bot = bot
        self.collection: motor_asyncio.AsyncIOMotorCollection = self.bot.database["remind_data"]
        self.sendReminds.start()

    def cog_unload(self):
        self.sendReminds.stop()

    @commands.command(name="remind", aliases=("Remind", "りまいんど", "めざまし", "アラーム"), help="""\
毎日指定時間にメッセージを送信する
毎日（平日だろうが休日だろうが、雨の日だろうが落ち込んだ日だろうが（BOTが落ちてなければ））指定時間になったら、チャンネルに特定のメッセージを送信します。

・使い方
`n!remind on [時間(hh:mm)] [メッセージ内容...(複数行可)]`
`n!remind off [時間(hh:mm)]`
`n!remind list`

メッセージ内に`%date%`と入力すると、その日の日付(`MM/DD`)に置き換わります。

・例
```
n!remind on 8:25 おはようございます！
今日は%date%です！
```
`n!remind off 08:25`
`n!remind list`""")
    async def remind(self, ctx: commands.Context):
        args = ctx.message.content.split(" ", 3)
        if len(args) < 2:
            await ctx.reply(embed=nextcord.Embed(title="使い方", description=f"`{self.bot.command_prefix}remind on [時間(hh:mm)] [メッセージ内容...(複数行可)]`\n`{self.bot.command_prefix}remind off [時間(hh:mm)]`\n`{self.bot.command_prefix}remind list`\n\n詳しくは`{self.bot.command_prefix}help remind`を参照してください。", color=0xff0000))
            return

        if args[1] == "on":
            if not admin_check.admin_check(ctx.guild, ctx.author):
                await ctx.reply(embed=nextcord.Embed(title="エラー", description="管理者権限がありません。", color=0xff0000))
                return

            if len(args) != 4:
                await ctx.reply(f"・エラー\n引数が足りません。\n`{self.bot.command_prefix}remind on [時間(hh:mm)] [メッセージ内容...(複数行可)]`")
                return

            if len(args[2]) > 5 or len(args[2]) < 3:
                await ctx.reply(f"・エラー\n時間の入力が不正です。\n`{self.bot.command_prefix}remind on [時間(hh:mm)] [メッセージ内容...(複数行可)]`")
                return

            time = TIME_CHECK.fullmatch(args[2])
            if time is None:
                await ctx.reply(f"・エラー\n時間の入力が不正です。\n`{self.bot.command_prefix}remind on [時間(hh:mm)] [メッセージ内容...(複数行可)]`")
                return

            time = time.group()
            if int(time.split(":")[0]) > 23 or int(time.split(":")[1]) > 59:
                await ctx.reply(f"・エラー\n時間の入力が不正です。\n`{self.bot.command_prefix}remind on [時間(hh:mm)] [メッセージ内容...(複数行可)]`")
                return

            time = ":".join([f"0{i}"[-2:] for i in time.split(":", 1)])

            await self.collection.update_one({"channel_id": ctx.channel.id}, {"$set": {"message": arg[3], "time": time}}, upsert=True)
            await ctx.reply(embed=nextcord.Embed(title="設定完了", description=f"毎日`{time}`に <#{ctx.channel.id}> にリマインドメッセージを送信します。", color=0x00ff00))
            return

        elif args[1] == "off":
            if not admin_check.admin_check(ctx.guild, ctx.author):
                await ctx.reply(embed=nextcord.Embed(title="エラー", description="管理者権限がありません。", color=0xff0000))
                return

            if len(args) != 3:
                await ctx.reply(f"・エラー\n引数が足りません。\n`{self.bot.command_prefix}remind off [時間(hh:mm)]`")
                return

            time = TIME_CHECK.fullmatch(args[2])
            if time is None:
                await ctx.reply(f"・エラー\n時間の入力が不正です。\n`{self.bot.command_prefix}remind off [時間(hh:mm)]`")
                return

            time = time.group()
            if int(time.split(":")[0]) > 23 or int(time.split(":")[1]) > 59:
                await ctx.reply(f"・エラー\n時間の入力が不正です。\n`{self.bot.command_prefix}remind off [時間(hh:mm)]`")
                return
            time = ":".join([f"0{i}"[-2:] for i in time.split(":", 1)])
            
            result = await self.collection.delete_one({"channel_id": ctx.channel.id, "time": time})
            
            if result is None!
                await ctx.reply(f"・エラー\nこのチャンネル`{ctx.channel.name}`で`{time}`に送信されるリマインドメッセージはありません。\n`{self.bot.command_prefix}remind off [時間(hh:mm)]`")
            else:
                await ctx.reply(embed=nextcord.Embed(title="削除完了", description=f"<#{ctx.channel.id}> での`{time}`のリマインドメッセージを削除しました。", color=

        elif args[1] == "list":
            reminds = await self.collection.find({"channel_id": ctx.channel.id}).to_list(length=None)
            if len(reminds) == 0:
                await ctx.reply(f"・エラー\nこのチャンネル`{ctx.channel.name}`で設定されているリマインドメッセージはありません。\n`{self.bot.command_prefix}remind list`")
                return

            embed = nextcord.Embed(
                title="リマインドメッセージ一覧",
                description=f"<#{ctx.channel.id}>",
                color=0x00ff00
            )
            for remind in reminds:
                embed.add_field(
                    name=remind["time"],
                    value=remind["message"],
                    inline=False
                )
            await ctx.reply(embed=embed)
            return

        else:
            await ctx.reply(embed=nextcord.Embed(
                title="使い方",
                description=f"`{self.bot.command_prefix}remind on [時間(hh:mm)] [メッセージ内容...(複数行可)]`\n`{self.bot.command_prefix}remind off [時間(hh:mm)]`\n`{self.bot.command_prefix}remind list`\n\n詳しくは`{self.bot.command_prefix}help remind`を参照してください。",
                color=0xff0000
            ))
            return

    @nextcord.slash_command(name="remind", description="remind", guild_ids=n_fc.GUILD_IDS)
    async def remind_slash(self, interaction: Interaction):
        pass

    @remind_slash.subcommand(name="on", description="Setting of Remind Message", description_localizations={nextcord.Locale.ja: "リマインドメッセージの設定"})
    async def on_remind_slash(self, interaction: Interaction):
        if admin_check.admin_check(interaction.guild, interaction.user):
            modal = RemindMaker(self.collection)
            await interaction.response.send_modal(modal=modal)
            return
        else:
            await interaction.response.send_text("管理者権限がありません。")
            return

    @remind_slash.subcommand(name="off", description="Delete Remind Message Setting", description_localizations={nextcord.Locale.ja: "リマインドメッセージの削除"})
    async def off_remind_slash(self, interaction: Interaction, time: str = SlashOption(name="time", description="リマインドの時間", required=True)):
        if admin_check.admin_check(interaction.guild, interaction.user):
            await interaction.response.defer(ephemeral=True)

            timeD = TIME_CHECK.fullmatch(time)
            if timeD is None:
                await interaction.send("・エラー\n時間の入力が不正です。\n`/remind off time:[時間(hh:mm)]`", ephemeral=True)
                return

            timeB = timeD.group()
            if int(timeB.split(":")[0]) > 23 or int(timeB.split(":")[1]) > 59:
                await interaction.send("・エラー\n時間の入力が不正です。\n`/remind off time:[時間(hh:mm)]`", ephemeral=True)
                return

            timeB = ":".join([f"0{i}"[-2:] for i in timeB.split(":", 1)])
            
            result = await self.collection.delete_one({"channel_id": interaction.channel.id, "time": timeB})

            if result is None:
                await interaction.send(f"・エラー\nこのチャンネル`{interaction.channel.name}`で`{timeB}`に送信されるリマインドメッセージはありません。\n`/remind off time:[時間(hh:mm)]`", ephemeral=True)
            else:
                await interaction.send(embed=nextcord.Embed(title="削除完了", description=f"<#{interaction.channel.id}> での`{timeB}`のリマインドメッセージを削除しました。", color=0x00ff00))
        else:
            await interaction.send("管理者権限がありません。", ephemeral=True)
            return

    @remind_slash.subcommand(name="list", description="List Remind Messages", description_localizations={nextcord.Locale.ja: "リマインドメッセージ一覧"})
    async def list_remind_slash(self, interaction: Interaction):
        await interaction.response.defer()
        reminds = await self.collection.find({"channel_id": ctx.channel.id}).find(length=None)
        
        if len(reminds) == 0:
            await interaction.followup.send(f"・エラー\nこのチャンネル`{interaction.channel.name}`で設定されているリマインドメッセージはありません。\n`/remind list`")
            return

        embed = nextcord.Embed(
            title="リマインドメッセージ一覧",
            description=f"<#{interaction.channel.id}>",
            color=0x00ff00
        )
        for remind in reminds:
            embed.add_field(
                name=remind["time"],
                value=remind["message"],
                inline=False
            )
        await interaction.followup.send(embed=embed)
        return

    @tasks.loop(minutes=1)
    async def sendReminds(self):
        await self.bot.wait_until_ready()
        dt = datetime.datetime.now()
        now_time = dt.strftime("%H:%M")
        reminds = await self.collection.delete_one({"time": now_time})
        for remind in reminds:
            try:
                message = remind["message"].replace("%date%", dt.strftime("%m/%d"))
                CHANNEL = await self.bot.fetch_channel(int(remind["channel_id"]))
                await CHANNEL.send(message)
            except Exception as err:
                logging.error(f"ERR:{err}\n{remind['channel_id']}")


def setup(bot, **kwargs):
    bot.add_cog(Remind(bot, **kwargs))


def teardown(bot):
    logging.info(f"Pin teardown")
