import asyncio
from nextcord.ext import commands, tasks
import nextcord
import os, sys, json, datetime
from nextcord import Interaction, SlashOption, ChannelType
import traceback
from re import compile
sys.path.append('../')
from util import admin_check, n_fc, eh, database

# りまいんど

TIME_CHECK = compile(r"[0-9]{1,2}:[0-9]{1,2}")

#loggingの設定
import logging
dir = sys.path[0]
class NoTokenLogFilter(logging.Filter):
    def filter(self, record):
        message = record.getMessage()
        return 'token' not in message

logger = logging.getLogger(__name__)
logger.addFilter(NoTokenLogFilter())
formatter = '%(asctime)s$%(filename)s$%(lineno)d$%(funcName)s$%(levelname)s:%(message)s'
logging.basicConfig(format=formatter, filename=f'{dir}/nira.log', level=logging.INFO)



DBS = database.openSheet()
DATABASE_KEY = "B5"
RemindData = {}
# {channel_id:{"00:00":"message"}}


def readDatabase() -> None:
    if DBS.acell(DATABASE_KEY).value != "" and DBS.acell(DATABASE_KEY).value is not None:
        global RemindData
        RemindData = json.loads(DBS.acell(DATABASE_KEY).value)
        RemindDataTemp = {}
        for key, value in RemindData.items():
            RemindDataTemp[int(key)] = value
        RemindData = RemindDataTemp
    return


def writeDatabase() -> None:
    DBS.update_acell(DATABASE_KEY,json.dumps(RemindData))
    return




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
        
        time = ":".join([f"0{i}"[-2:] for i in time.split(":",1)])

        if interaction.channel.id not in RemindData:
            RemindData[interaction.channel.id] = {}

        if time in RemindData[interaction.channel.id]:
            await interaction.followup.send("・エラー\n指定時間には既にメッセージが設定されています。\n一度オフにしてから再度指定しなおしてください。\n", ephemeral=True)
            return

        RemindData[interaction.channel.id][time] = self.remind_content.value
        writeDatabase()
        await interaction.followup.send(embed=nextcord.Embed(title="設定完了", description=f"毎日`{time}`に <#{interaction.channel.id}> にリマインドメッセージを送信します。",color=0x00ff00))
        return



class Remind(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot


    @commands.command(name="remind", aliases=("Remind","りまいんど","めざまし","アラーム"), help="""\
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
        if ctx.author.id != 669178357371371522:
            return
        args = ctx.message.content.split(" ", 3)
        if len(args) < 2:
            await ctx.reply(embed=nextcord.Embed(title="使い方", description="`n!remind on [時間(hh:mm)] [メッセージ内容...(複数行可)]`\n`n!remind off [時間(hh:mm)]`\n`n!remind list`\n\n詳しくは`n!help remind`を参照してください。",color=0xff0000))
            return
        if args[1] == "on":
            if not admin_check.admin_check(ctx.guild, ctx.author):
                await ctx.reply(embed=nextcord.Embed(title="エラー", description="管理者権限がありません。",color=0xff0000))
                return

            if len(args) != 4:
                await ctx.reply("・エラー\n引数が足りません。\n`n!remind on [時間(hh:mm)] [メッセージ内容...(複数行可)]`")
                return

            if len(args[2]) > 5 or len(args[2]) < 3:
                await ctx.reply("・エラー\n時間の入力が不正です。\n`n!remind on [時間(hh:mm)] [メッセージ内容...(複数行可)]`")
                return

            time = TIME_CHECK.fullmatch(args[2])
            if time is None:
                await ctx.reply("・エラー\n時間の入力が不正です。\n`n!remind on [時間(hh:mm)] [メッセージ内容...(複数行可)]`")
                return

            time = time.group()
            if int(time.split(":")[0]) > 23 or int(time.split(":")[1]) > 59:
                await ctx.reply("・エラー\n時間の入力が不正です。\n`n!remind on [時間(hh:mm)] [メッセージ内容...(複数行可)]`")
                return
            
            time = ":".join([f"0{i}"[-2:] for i in time.split(":",1)])

            if ctx.channel.id not in RemindData:
                RemindData[ctx.channel.id] = {}

            if time in RemindData[ctx.channel.id]:
                await ctx.reply("・エラー\n指定時間には既にメッセージが設定されています。\n一度オフにしてから再度指定しなおしてください。\n`n!remind on [時間(hh:mm)] [メッセージ内容...(複数行可)]`")
                return

            RemindData[ctx.channel.id][time] = args[3]
            writeDatabase()
            await ctx.reply(embed=nextcord.Embed(title="設定完了", description=f"毎日`{time}`に <#{ctx.channel.id}> にリマインドメッセージを送信します。",color=0x00ff00))
            return

        elif args[1] == "off":
            if not admin_check.admin_check(ctx.guild, ctx.author):
                await ctx.reply(embed=nextcord.Embed(title="エラー", description="管理者権限がありません。",color=0xff0000))
                return

            if len(args) != 3:
                await ctx.reply("・エラー\n引数が足りません。\n`n!remind off [時間(hh:mm)]`")
                return

            time = TIME_CHECK.fullmatch(args[2])
            if time is None:
                await ctx.reply("・エラー\n時間の入力が不正です。\n`n!remind off [時間(hh:mm)]`")
                return

            time = time.group()
            if int(time.split(":")[0]) > 23 or int(time.split(":")[1]) > 59:
                await ctx.reply("・エラー\n時間の入力が不正です。\n`n!remind off [時間(hh:mm)]`")
                return
            time = ":".join([f"0{i}"[-2:] for i in time.split(":",1)])

            if ctx.channel.id not in RemindData:
                await ctx.reply(f"・エラー\nこのチャンネル`{ctx.channel.name}`で設定されているリマインドメッセージはありません。\n`n!remind off [時間(hh:mm)]`")
                return

            if time not in RemindData[ctx.channel.id]:
                await ctx.reply(f"・エラー\nこのチャンネル`{ctx.channel.name}`で`{time}`に送信されるリマインドメッセージはありません。\n`n!remind off [時間(hh:mm)]`")
                return

            del RemindData[ctx.channel.id][time]
            writeDatabase()
            await ctx.reply(embed=nextcord.Embed(title="削除完了", description=f"<#{ctx.channel.id}> での`{time}`のリマインドメッセージを削除しました。", color=0x00ff00))
            return

        elif args[1] == "list":
            if ctx.channel.id not in RemindData:
                await ctx.reply(f"・エラー\nこのチャンネル`{ctx.channel.name}`で設定されているリマインドメッセージはありません。\n`n!remind list`")
                return

            embed = nextcord.Embed(title="リマインドメッセージ一覧", description=f"<#{ctx.channel.id}>", color=0x00ff00)
            for time in RemindData[ctx.channel.id]:
                embed.add_field(name=time, value=RemindData[ctx.channel.id][time], inline=False)
            await ctx.reply(embed=embed)
            return
        
        elif args[1] == "debug":
            if ctx.author.id in n_fc.py_admin:
                command = args[2]
                if command == "current":
                    await ctx.reply(f"```py\n[SHOW] Device\n{RemindData}```")
                    return
                elif command == "server":
                    await ctx.reply(f"```py\n[SHOW] Server\n{DBS.acell(DATABASE_KEY).value}```")
                    return
                elif command == "write":
                    writeDatabase()
                    await ctx.reply(f"```py\n[PUSH] Push data to server.\nDevice -> Server\nSuccess.```")
                    return
                elif command == "read":
                    readDatabase()
                    await ctx.reply(f"```py\n[PULL] Pull data from server.\nServer -> Device\nSuccess.```")
                    return
                else:
                    await ctx.reply(f"""\
```sh
[HELP] Database Manager

n!remind debug [command]

current - Show UpperData of device
server - Show UpperData of server
write - write UpperData of device to server
read - read UpperData from server to device```""")
                    return
            else:
                await ctx.reply("管理者権限がありません。")
                return
        else:
            await ctx.reply(embed=nextcord.Embed(title="使い方", description="`n!remind on [時間(hh:mm)] [メッセージ内容...(複数行可)]`\n`n!remind off [時間(hh:mm)]`\n`n!remind list`\n\n詳しくは`n!help remind`を参照してください。",color=0xff0000))
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
            
            timeB = ":".join([f"0{i}"[-2:] for i in timeB.split(":",1)])

            if interaction.channel.id not in RemindData:
                await interaction.followup.send(f"・エラー\nこのチャンネル`{interaction.channel.name}`で設定されているリマインドメッセージはありません。\n`/remind off time:[時間(hh:mm)]`", ephemeral=True)
                return

            if timeB not in RemindData[interaction.channel.id]:
                await interaction.followup.send(f"・エラー\nこのチャンネル`{interaction.channel.name}`で`{timeB}`に送信されるリマインドメッセージはありません。\n`/remind off time:[時間(hh:mm)]`", ephemeral=True)
                return

            del RemindData[interaction.channel.id][timeB]
            writeDatabase()
            await interaction.followup.send(embed=nextcord.Embed(title="削除完了", description=f"<#{interaction.channel.id}> での`{timeB}`のリマインドメッセージを削除しました。", color=0x00ff00))
            return
        else:
            await interaction.response.send_text("管理者権限がありません。")
            return


    @remind_slash.subcommand(name="list", description="リマインドメッセージ一覧")
    async def list_remind_slash(self, interaction: Interaction):
        await interaction.response.defer()

        if interaction.channel.id not in RemindData:
            await interaction.followup.send(f"・エラー\nこのチャンネル`{interaction.channel.name}`で設定されているリマインドメッセージはありません。\n`/remind list`")
            return

        embed = nextcord.Embed(title="リマインドメッセージ一覧", description=f"<#{interaction.channel.id}>", color=0x00ff00)
        for time in RemindData[interaction.channel.id]:
            embed.add_field(name=time, value=RemindData[interaction.channel.id][time], inline=False)
        await interaction.followup.send(embed=embed)
        return


    @tasks.loop(minutes=1)
    async def sendReminds(self):
        await self.bot.wait_until_ready()
        dt = datetime.datetime.now()
        now_time = dt.strftime("%H:%M")
        for channel, messages in RemindData.items():
            for time in messages.keys():
                if time == now_time:
                    try:
                        message = RemindData[channel][time]
                        Ch = await self.bot.fetch_channel(int(channel))
                        await Ch.send(message)
                    except BaseException as err:
                        logging.error(f"ERR:{err}\n{channel}")



def setup(bot):
    bot.add_cog(Remind(bot))
    readDatabase()
    Remind.sendReminds.start(Remind(bot))

def teardown(bot):
    logging.info("Pin teradown!")
    Remind.sendReminds.stop()
