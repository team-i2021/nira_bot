import asyncio
import datetime
import json
import logging
import os
import sys
import traceback
from re import compile

import HTTP_db
import nextcord
from nextcord import Interaction, SlashOption, ChannelType
from nextcord.ext import commands, tasks

from util import admin_check, n_fc, eh, database, dict_list
from util.nira import NIRA

# りまいんど

TIME_CHECK = compile(r"[0-9]{1,2}:[0-9]{1,2}")

REMIND_DATA = {}
DATABASE_KEY = "remind_data"

# {channel_id:{"00:00":"message"}}
# [[channel_id, ["00:00","message"]]]

async def pullData(client: HTTP_db.Client):
    global REMIND_DATA
    if not await client.exists(DATABASE_KEY):
        await client.post(DATABASE_KEY, [])
    try:
        TEMP_DATA = await client.get(DATABASE_KEY)
        if TEMP_DATA == []:
            REMIND_DATA = {}
            return True
        REMIND_DATA = {i[0]: {i[1][0]: i[1][1]} for i in TEMP_DATA}
        return True
    except Exception:
        logging.error(traceback.format_exc())
        REMIND_DATA = {}


async def pushData(client: HTTP_db.Client):
    global REMIND_DATA
    if not await client.exists(DATABASE_KEY):
        await client.post(DATABASE_KEY, [])
        return True
    try:
        post_data = []
        for key, value in REMIND_DATA.items():
            tmp = [key]
            for time, content in value.items():
                tmp.append([time, content])
            post_data.append(tmp)
        await client.post(DATABASE_KEY, post_data)
        return True
    except Exception as err:
        logging.error(traceback.format_exc())
        raise err


class RemindMaker(nextcord.ui.Modal):
    def __init__(self):
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

        if interaction.channel.id not in REMIND_DATA:
            REMIND_DATA[interaction.channel.id] = {}

        if time in REMIND_DATA[interaction.channel.id]:
            await interaction.followup.send("・エラー\n指定時間には既にメッセージが設定されています。\n一度オフにしてから再度指定しなおしてください。\n", ephemeral=True)
            return

        REMIND_DATA[interaction.channel.id][time] = self.remind_content.value
        await pushData(self.client)
        await interaction.followup.send(embed=nextcord.Embed(title="設定完了", description=f"毎日`{time}`に <#{interaction.channel.id}> にリマインドメッセージを送信します。", color=0x00ff00))
        return


class Remind(commands.Cog):
    def __init__(self, bot: NIRA, **kwargs):
        self.bot = bot
        asyncio.ensure_future(pullData(self.bot.client))
        self.sendReminds.start()

    def cog_unload(self):
        self.sendReminds.stop()

    @commands.command(name="remind", aliases=("Remind", "りまいんど", "めざまし", "アラーム"), help="""\
毎日指定時間にメッセージを送信する
毎日（平日だろうが休日だろうが、雨の日だろうが落ち込んだ日だろうが）指定時間になったら、チャンネルに特定のメッセージを送信します。

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

            if ctx.channel.id not in REMIND_DATA:
                REMIND_DATA[ctx.channel.id] = {}

            if time in REMIND_DATA[ctx.channel.id]:
                await ctx.reply(f"・エラー\n指定時間には既にメッセージが設定されています。\n一度オフにしてから再度指定しなおしてください。\n`{self.bot.command_prefix}remind on [時間(hh:mm)] [メッセージ内容...(複数行可)]`")
                return

            REMIND_DATA[ctx.channel.id][time] = args[3]
            await pushData(self.bot.client)
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

            if ctx.channel.id not in REMIND_DATA:
                await ctx.reply(f"・エラー\nこのチャンネル`{ctx.channel.name}`で設定されているリマインドメッセージはありません。\n`{self.bot.command_prefix}remind off [時間(hh:mm)]`")
                return

            if time not in REMIND_DATA[ctx.channel.id]:
                await ctx.reply(f"・エラー\nこのチャンネル`{ctx.channel.name}`で`{time}`に送信されるリマインドメッセージはありません。\n`{self.bot.command_prefix}remind off [時間(hh:mm)]`")
                return

            del REMIND_DATA[ctx.channel.id][time]
            if len(REMIND_DATA[ctx.channel.id]) == 0:
                del REMIND_DATA[ctx.channel.id]
            await pushData(self.bot.client)
            await ctx.reply(embed=nextcord.Embed(title="削除完了", description=f"<#{ctx.channel.id}> での`{time}`のリマインドメッセージを削除しました。", color=0x00ff00))
            return

        elif args[1] == "list":
            if ctx.channel.id not in REMIND_DATA:
                await ctx.reply(f"・エラー\nこのチャンネル`{ctx.channel.name}`で設定されているリマインドメッセージはありません。\n`{self.bot.command_prefix}remind list`")
                return

            embed = nextcord.Embed(
                title="リマインドメッセージ一覧", description=f"<#{ctx.channel.id}>", color=0x00ff00)
            for time in REMIND_DATA[ctx.channel.id]:
                embed.add_field(
                    name=time, value=REMIND_DATA[ctx.channel.id][time], inline=False)
            await ctx.reply(embed=embed)
            return

        elif args[1] == "db":
            if await self.bot.is_owner(ctx.author):
                command = args[2]
                if command == "local":
                    await ctx.reply(f"```py\n[SHOW] Local\n{REMIND_DATA}```")
                    return
                elif command == "remote":
                    await ctx.reply(f"```py\n[SHOW] Remote\n{await self.bot.client.get(DATABASE_KEY)}```")
                    return
                elif command == "push":
                    await pushData(self.bot.client)
                    await ctx.reply(f"```py\n[PUSH] Push data to server.\nDevice -> Server\nSuccess.```")
                    return
                elif command == "pull":
                    await pullData(self.bot.client)
                    await ctx.reply(f"```py\n[PULL] Pull data from server.\nServer -> Device\nSuccess.```")
                    return
                else:
                    await ctx.reply(f"""\
```sh
[HELP] Database Manager

n!remind db [command]

local - Show data of local
remote - Show data of remote
push - push data of device to server
pull - pull data from server to device```""")
                    return
            else:
                await ctx.reply("管理者権限がありません。")
                return
        else:
            await ctx.reply(embed=nextcord.Embed(title="使い方", description=f"`{self.bot.command_prefix}remind on [時間(hh:mm)] [メッセージ内容...(複数行可)]`\n`{self.bot.command_prefix}remind off [時間(hh:mm)]`\n`{self.bot.command_prefix}remind list`\n\n詳しくは`{self.bot.command_prefix}help remind`を参照してください。", color=0xff0000))
            return

    @nextcord.slash_command(name="remind", description="remind", guild_ids=n_fc.GUILD_IDS)
    async def remind_slash(self, interaction: Interaction):
        pass

    @remind_slash.subcommand(name="on", description="リマインドメッセージの設定")
    async def on_remind_slash(self, interaction: Interaction):
        if admin_check.admin_check(interaction.guild, interaction.user):
            modal = RemindMaker()
            await interaction.response.send_modal(modal=modal)
            return
        else:
            await interaction.response.send_text("管理者権限がありません。")
            return

    @remind_slash.subcommand(name="off", description="リマインドメッセージの削除")
    async def off_remind_slash(self, interaction: Interaction, time: str = SlashOption(name="time", description="リマインドの時間", required=True)):
        if admin_check.admin_check(interaction.guild, interaction.user):
            await interaction.response.defer()

            timeD = TIME_CHECK.fullmatch(time)
            if timeD is None:
                await interaction.followup.send("・エラー\n時間の入力が不正です。\n`/remind off time:[時間(hh:mm)]`", ephemeral=True)
                return

            timeB = timeD.group()
            if int(timeB.split(":")[0]) > 23 or int(timeB.split(":")[1]) > 59:
                await interaction.followup.send("・エラー\n時間の入力が不正です。\n`/remind off time:[時間(hh:mm)]`", ephemeral=True)
                return

            timeB = ":".join([f"0{i}"[-2:] for i in timeB.split(":", 1)])

            if interaction.channel.id not in REMIND_DATA:
                await interaction.followup.send(f"・エラー\nこのチャンネル`{interaction.channel.name}`で設定されているリマインドメッセージはありません。\n`/remind off time:[時間(hh:mm)]`", ephemeral=True)
                return

            if timeB not in REMIND_DATA[interaction.channel.id]:
                await interaction.followup.send(f"・エラー\nこのチャンネル`{interaction.channel.name}`で`{timeB}`に送信されるリマインドメッセージはありません。\n`/remind off time:[時間(hh:mm)]`", ephemeral=True)
                return

            del REMIND_DATA[interaction.channel.id][timeB]
            if len(REMIND_DATA[interaction.channel.id]) == 0:
                del REMIND_DATA[interaction.channel.id]
            await pushData(self.bot.client)
            await interaction.followup.send(embed=nextcord.Embed(title="削除完了", description=f"<#{interaction.channel.id}> での`{timeB}`のリマインドメッセージを削除しました。", color=0x00ff00))
            return
        else:
            await interaction.response.send_text("管理者権限がありません。")
            return

    @remind_slash.subcommand(name="list", description="リマインドメッセージ一覧")
    async def list_remind_slash(self, interaction: Interaction):
        await interaction.response.defer()

        if interaction.channel.id not in REMIND_DATA:
            await interaction.followup.send(f"・エラー\nこのチャンネル`{interaction.channel.name}`で設定されているリマインドメッセージはありません。\n`/remind list`")
            return

        embed = nextcord.Embed(
            title="リマインドメッセージ一覧", description=f"<#{interaction.channel.id}>", color=0x00ff00)
        for time in REMIND_DATA[interaction.channel.id]:
            embed.add_field(
                name=time, value=REMIND_DATA[interaction.channel.id][time], inline=False)
        await interaction.followup.send(embed=embed)
        return

    @tasks.loop(minutes=1)
    async def sendReminds(self):
        await self.bot.wait_until_ready()
        dt = datetime.datetime.now()
        now_time = dt.strftime("%H:%M")
        for channel, messages in REMIND_DATA.items():
            for time in messages.keys():
                if time == now_time:
                    try:
                        message = REMIND_DATA[channel][time].replace(
                            "%date%", dt.strftime("%m/%d"))
                        Ch = await self.bot.fetch_channel(int(channel))
                        await Ch.send(message)
                    except Exception as err:
                        logging.error(f"ERR:{err}\n{channel}")


def setup(bot, **kwargs):
    bot.add_cog(Remind(bot, **kwargs))


def teardown(bot):
    logging.info(f"Pin teardown")
