import datetime
import pickle
import sys

import nextcord
from nextcord import SlashOption, Interaction
from nextcord.ext import commands

sys.path.append('../')
import asyncio
import datetime
import importlib
#loggingの設定
import logging
import os
import re, importlib

PREFIX = "n!"

home_dir = os.path.dirname(__file__)[:-4]

dir = sys.path[0]
from util import admin_check, eh, n_fc, server_check
import traceback

class NoTokenLogFilter(logging.Filter):
    def filter(self, record):
        message = record.getMessage()
        return 'token' not in message

logger = logging.getLogger(__name__)
logger.addFilter(NoTokenLogFilter())
formatter = '%(asctime)s$%(filename)s$%(lineno)d$%(funcName)s$%(levelname)s:%(message)s'
logging.basicConfig(format=formatter, filename=f'{dir}/nira.log', level=logging.INFO)

ss_check_result = {}


ss_commands = f"""・SS系コマンド一覧
`{PREFIX}ss`: 登録されているサーバーのステータスを表示します。
`{PREFIX}ss add [表示名] [アドレス],[ポート]`: サーバーを追加します。
`{PREFIX}ss list`: 登録されているサーバーの一覧を表示します。
`{PREFIX}ss auto on [*ユーザーID]`: SSAutoで、鯖落ちが起きたら通知します。ユーザーIDを指定すると、指定されたIDにメンションします。指定されなかった場合は、メッセージを送ったユーザーをメンションします。
`{PREFIX}ss auto force [*チャンネルID] [*メッセージID]`: 10分毎にステータスを更新するAutoSSのメッセージを送信します。「このBOTが送信したメッセージ」のチャンネルID及びメッセージIDを指定すると、そのメッセージをAutoSSのメッセージに変更します。
`{PREFIX}ss auto off`: AutoSSを停止します。
`{PREFIX}ss edit [サーバーID] [表示名] [アドレス],[ポート]`: 指定したサーバーIDの表示名やアドレスなどを修正します。事前に`{PREFIX}ss list`などで確認しておくことを推奨します。
`{PREFIX}ss sort [サーバーID1] [サーバーID2]`: サーバーID1とサーバID2の場所を入れ替えます。
`{PREFIX}ss del [サーバーID]`: 指定したサーバーIDの情報を削除します。
`{PREFIX}ss del all`: 登録されているサーバーをすべて削除します。
`{PREFIX}ss all`: 登録されているサーバーのステータスをより詳細に表示します。あまりにサーバー数があると、メッセージ数規定に引っかかって送れない場合があります。
`{PREFIX}ss [サーバーID]`: 指定したサーバーIDのステータスのみを表示します。
"""

async def ss_force(loop, message:nextcord.Message):
    await message.edit(content="Loading status...",view=None)
    while True:
        try:
            embed = nextcord.Embed(title="ServerStatus Checker", description=f"LastCheck:{datetime.datetime.now()}", color=0x00ff00)
            for i in range(int(n_fc.steam_server_list[message.guild.id]["value"])):
                await server_check.ss_pin_async(loop, embed, message.guild.id, i + 1)
            await message.edit(f"AutoSS実行中\n止めるには`n!ss auto off`\n再試行するには`n!ss auto force {message.channel.id} {message.id}`又は`/reload`", embed=embed, view=server_status.Reload_SS_Auto())
            logging.info("Status loaded.")
            await asyncio.sleep(60*10)
        except BaseException as err:
            logging.info(err,traceback.format_exc())
            await message.edit(content=f"err:{err}")
            await ss_force(loop, message)

#async def ss_pin(self, ment_id, message):
#    ss_check_result[message.guild.id] = {}
#    await message.edit(content=f"チェックシステムを有効化しています...")
#    logging.info(f"{message.guild.name}にてAutoSSが有効になりました。")
#    while True:
#        await message.edit(content=f"現在チェックを行っています...\n最終チェック時刻：`{datetime.datetime.now()}`")
#        logging.info(f"{message.guild.name}でのAutoSSチェックを実行します。")
#        for i in map(str, range(1, int(n_fc.steam_server_list[message.guild.id]["value"])+1)):
#            if await server_check.server_check_loop(self.bot.loop, message.guild.id, i) == False:
#                # 鯖落ちしてかもるよ
#                await message.edit(content=f"チェック結果：失敗(1/3)\n最終チェック時刻：`{datetime.datetime.now()}`")
#                logging.error(f"{message.guild.name}でのAutoSSチェック結果：失敗（1/3回目）")
#                await asyncio.sleep(5)
#                if await server_check.server_check_loop(self.bot.loop, message.guild.id, i) == False:
#                    await message.edit(content=f"チェック結果：失敗(2/3)\n最終チェック時刻：`{datetime.datetime.now()}`")
#                    logging.error(f"{message.guild.name}でのAutoSSチェック結果：失敗（2/3回目）")
#                    await asyncio.sleep(5)
#                    if await server_check.server_check_loop(self.bot.loop, message.guild.id, i) == False:
#                        await message.edit(content=f"チェック結果：失敗(3/3)\n最終チェック時刻：`{datetime.datetime.now()}`")
#                        logging.error(f"{message.guild.name}でのAutoSSチェック結果：失敗（3/3回目）")
#                        await message.edit(content=f"チェック結果：失敗(メッセージを送信して終了します。)\n最終チェック時刻：`{datetime.datetime.now()}`")
#                        await message.channel.send(f"<@{ment_id}> - もしかして鯖落ちしてたりしません...？\n\nAutoSSが無効になりました。\n一応`n!ss`で確認してみましょう！")
#                        del n_fc.pid_ss[message.guild.id]
#                        return False
#            # 正常だよ
#            logging.info(f"{message.guild.name}でのAutoSSチェック結果：成功")
#            await message.edit(content=f"最後のチェック結果：成功\n最終チェック時刻：`{datetime.datetime.now()}`")
#            await asyncio.sleep(5)
#        await asyncio.sleep(60*30) # 60秒*30＝30分

async def get_mes(bot, channel_id, message_id):
    ch_obj = await bot.fetch_channel(channel_id)
    messs = await ch_obj.fetch_message(message_id)
    return messs

async def launch_ss(bot, channel_id, message_id):
    ch_obj = await bot.fetch_channel(channel_id)
    messs = await ch_obj.fetch_message(message_id)
    await ss_force(bot, messs)

async def ss_loop_goes(self, ment_id, message):
    ss_check_result[message.guild.id] = {}
    await message.edit(content=f"実行されています。")
    logging.info(f"{message.guild.name}にてAutoSSが有効になりました。")
    while True:
        await message.edit(content=f"現在チェックを行っています...\n最終チェック時刻：`{datetime.datetime.now()}`")
        logging.info(f"{message.guild.name}でのAutoSSチェックを実行します。")
        for i in map(str, range(1, int(n_fc.steam_server_list[message.guild.id]["value"])+1)):
            if await server_check.server_check_loop(self.bot.loop, message.guild.id, i) == False:
                # 鯖落ちしてかもるよ
                await message.edit(content=f"チェック結果：失敗(1/3)\n最終チェック時刻：`{datetime.datetime.now()}`")
                logging.error(f"{message.guild.name}でのAutoSSチェック結果：失敗（1/3回目）")
                await asyncio.sleep(5)
                if await server_check.server_check_loop(self.bot.loop, message.guild.id, i) == False:
                    await message.edit(content=f"チェック結果：失敗(2/3)\n最終チェック時刻：`{datetime.datetime.now()}`")
                    logging.error(f"{message.guild.name}でのAutoSSチェック結果：失敗（2/3回目）")
                    await asyncio.sleep(5)
                    if await server_check.server_check_loop(self.bot.loop, message.guild.id, i) == False:
                        await message.edit(content=f"チェック結果：失敗(3/3)\n最終チェック時刻：`{datetime.datetime.now()}`")
                        logging.error(f"{message.guild.name}でのAutoSSチェック結果：失敗（3/3回目）")
                        await message.edit(content=f"チェック結果：失敗(メッセージを送信して終了します。)\n最終チェック時刻：`{datetime.datetime.now()}`")
                        await message.channel.send(f"<@{ment_id}> - もしかして鯖落ちしてたりしません...？\n\nAutoSSが無効になりました。\n一応`n!ss`で確認してみましょう！")
                        return False
            # 正常だよ
            logging.info(f"{message.guild.name}でのAutoSSチェック結果：成功")
            await message.edit(content=f"最後のチェック結果：成功\n最終チェック時刻：`{datetime.datetime.now()}`")
            await asyncio.sleep(5)
        await asyncio.sleep(60*30) # 60秒*30＝30分


#コマンド内部
async def ss_base(self, ctx: commands.Context):
    if ctx.message.content == f"{PREFIX}ss":
        if ctx.message.guild.id not in n_fc.steam_server_list:
            await ctx.message.reply("サーバーは登録されていません。")
            return
        async with ctx.message.channel.typing():
            embed = nextcord.Embed(title="Server Status Checker", description=f"{ctx.message.author.mention}\n:globe_with_meridians:Status\n==========", color=0x00ff00)
            for i in map(str, range(1, int(n_fc.steam_server_list[ctx.message.guild.id]["value"])+1)):
                await server_check.server_check_async(self.bot.loop, embed, 0, ctx.message.guild.id, i)
            await asyncio.sleep(1)
            await ctx.message.reply(embed=embed, view=server_status.Recheck_SS_Embed())
        return
    args = ctx.message.content.split(" ")

    if args[1] == "add":
        if len(args) == 1:
            await ctx.message.reply("構文が異なります。\n```n!ss add [表示名] [IPアドレス],[ポート番号]```")
            return
        else:
            try:
                if ctx.guild.id not in n_fc.steam_server_list:
                    n_fc.steam_server_list[ctx.guild.id] = {"value": "0"}
                ad_name = str(args[2])
                address = " ".join(args[3:])
                ad_ip = str(re.sub("[^0-9a-zA-Z._-]", "", address.split(",")[0]))
                ad_port = int(re.sub("[^0-9]", "", address.split(",")[1]))
                sset_point = int(n_fc.steam_server_list[ctx.guild.id]["value"])
                n_fc.steam_server_list[ctx.guild.id][f"{sset_point + 1}_ad"] = (ad_ip, ad_port)
                n_fc.steam_server_list[ctx.guild.id][f"{sset_point + 1}_nm"] = ad_name
                n_fc.steam_server_list[ctx.guild.id]["value"] = str(sset_point + 1)
                await ctx.reply(f"サーバー名：{ad_name}\nサーバーアドレス: ({ad_ip},{ad_port})")
                with open(f'{home_dir}/steam_server_list.nira', 'wb') as f:
                    pickle.dump(n_fc.steam_server_list, f)
                return
            except BaseException as err:
                await ctx.reply(f"サーバー追加時にエラーが発生しました。\n```sh\n{err}```")
                return

    elif args[1] == "list":
        if ctx.guild.id not in n_fc.steam_server_list:
            await ctx.message.reply("サーバーは登録されていません。")
            return
        else:
            if admin_check.admin_check(ctx.guild, ctx.message.author) or ctx.message.author.id in n_fc.py_admin:
                user = await self.bot.fetch_user(ctx.message.author.id)
                embed = nextcord.Embed(title="Steam Server List", description=f"「{ctx.guild.name}」のサーバーリスト\n```保存数：{str(n_fc.steam_server_list[ctx.guild.id]['value'])}```", color=0x00ff00)
                for i in range(int(n_fc.steam_server_list[ctx.guild.id]['value'])):
                    embed.add_field(name=f"ID: `{i+1}`\n保存名: `{str(n_fc.steam_server_list[ctx.guild.id][f'{i+1}_nm'])}`", value=f"アドレス：`{str(n_fc.steam_server_list[ctx.guild.id][f'{i+1}_ad'])}`")
                await user.send(embed=embed)
                await ctx.message.add_reaction("\U00002705")
                return
            else:
                await ctx.message.reply(embed=nextcord.Embed(title="エラー", description="管理者権限がありません。", color=0xff0000))
                return

    elif args[1] == "auto":
        if admin_check.admin_check(ctx.guild, ctx.message.author) == False:
            await ctx.message.reply(embed=nextcord.Embed(title="エラー", description="管理者権限がありません。", color=0xff0000))
            return
        if ctx.message.content == "n!ss auto":
            await ctx.reply(embed=nextcord.Embed(title="エラー", description="引数が足りません。\n`n!ss auto on/off`"))
            return
        elif ctx.message.content[10:12] == "on":
            try:
                if ctx.guild.id not in n_fc.steam_server_list:
                    await ctx.reply("サーバーが登録されていません。")
                    return
                if len(ctx.message.content) <= 13:
                    ment_id = ctx.message.author.id
                else:
                    ment_id = str("".join(re.findall(r'[0-9]', ctx.message.content[13:])))
                    if ment_id == "":
                        await ctx.reply("ユーザーIDが不正です。\n`n!ss auto on [UserID]`")
                        return
                mes_ss = await ctx.channel.send(f"Starting process...")
                if ctx.guild.id in n_fc.pid_ss:
                    await mes_ss.edit(content=f"既に{ctx.guild.name}でタスクが実行されています。")
                    return
                n_fc.pid_ss[ctx.guild.id] = (self.bot.loop.create_task(ss_loop_goes(self, ment_id, mes_ss)), mes_ss)
                return
            except BaseException as err:
                await ctx.reply(embed=eh.eh(err))
                return
        elif ctx.message.content[10:13] == "off":
            if ctx.guild.id not in n_fc.pid_ss:
                await ctx.reply("既に無効になっているか、コマンドが実行されていません。")
                return
            try:
                if n_fc.pid_ss[ctx.guild.id][0].done() == False or ctx.guild.id in n_fc.pid_ss:
                    n_fc.pid_ss[ctx.guild.id][0].cancel()
                    del n_fc.pid_ss[ctx.guild.id]
                    del n_fc.force_ss_list[ctx.guild.id]
                    await ctx.reply("AutoSSを無効にしました。")
                    return
                else:
                    await ctx.reply("既に無効になっているか、コマンドが実行されていません。")
            except BaseException as err:
                await ctx.reply(embed=eh.eh(err))
                return
        elif ctx.message.content[10:15] == "force":
            if ctx.guild.id in n_fc.pid_ss:
                await ctx.reply(f"既に{ctx.guild.name}で他のAutoSSタスクが実行されています。")
                return
            if ctx.guild.id not in n_fc.steam_server_list:
                await ctx.reply("サーバーが登録されていません。")
                return
            mes_ss = await ctx.channel.send(f"Check your set message!")
            if ctx.guild.id in n_fc.pid_ss:
                await mes_ss.edit(content=f"既に{ctx.guild.name}でタスクが実行されています。")
                return
            if len(ctx.message.content) <= 16:
                n_fc.force_ss_list[ctx.guild.id] = [ctx.channel.id, mes_ss.id]
                n_fc.pid_ss[ctx.guild.id] = (self.bot.loop.create_task(ss_force(asyncio.get_event_loop(), mes_ss)),mes_ss)
                return
            else:
                try:
                    messs = await get_mes(self.bot, ctx.message.content[16:].split(" ",1)[0], ctx.message.content[16:].split(" ", 1)[1])
                except BaseException as err:
                    logging.error(err)
                    await ctx.reply("メッセージが見つかりませんでした。")
                    return
                await messs.edit(content="現在変更をしています...")
                n_fc.force_ss_list[ctx.guild.id] = [ctx.message.content[16:].split(" ",1)[0], ctx.message.content[16:].split(" ", 1)[1]]
                n_fc.pid_ss[ctx.guild.id] = (self.bot.loop.create_task(ss_force(asyncio.get_event_loop(), messs)),messs)
                return
        else:
            if ctx.guild.id not in n_fc.pid_ss:
                await ctx.reply("`n!ss auto [on/off]`\nAutoSSは無効になっています。")
                return
            try:
                if n_fc.pid_ss[ctx.guild.id][0].done() == True:
                    await ctx.reply("`n!ss auto [on/off]`\nAutoSSは無効になっています。")
                else:
                    await ctx.reply("`n!ss auto [on/off]`\nAutoSSは有効になっています。")
            except BaseException as err:
                await ctx.reply(embed=eh.eh(err))
                return
        return

    elif args[1] == "edit":
        if ctx.message.content == "n!ss edit":
            await ctx.message.reply("構文が異なります。\n```n!ss edit [サーバーナンバー] [名前] [IPアドレス],[ポート番号]```")
            return
        if ctx.guild.id not in n_fc.steam_server_list:
            await ctx.message.reply("サーバーは登録されていません。")
            return
        adre = ctx.message.content[10:].split(" ", 3)
        s_id = int("".join(re.findall(r'[0-9]', adre[0])))
        s_nm = str(adre[1])
        s_adre = str(adre[2]).split(",", 2)
        s_port = int(s_adre[1])
        s_ip = str(re.sub("[^0-9a-zA-Z._-]", "", s_adre[0]))
        b_value = int(n_fc.steam_server_list[ctx.guild.id]["value"])
        if b_value < s_id:
            await ctx.message.reply("そのサーバーナンバーのサーバーは登録されていません！\n`n!ss list`で確認してみてください。")
            return
        try:
            n_fc.steam_server_list[ctx.guild.id][f"{s_id}_ad"] = (s_ip, s_port)
            n_fc.steam_server_list[ctx.guild.id][f"{s_id}_nm"] = s_nm
            await ctx.message.reply(f"サーバーナンバー：{s_id}\nサーバー名: {s_nm}\nサーバーアドレス: ({s_ip},{s_port})")
            with open(f'{home_dir}/steam_server_list.nira', 'wb') as f:
                pickle.dump(n_fc.steam_server_list, f)
            return
        except BaseException as err:
            await ctx.message.reply(embed=eh.eh(err))
            return
    
    elif args[1] == "sort":
        if len(args) != 4:
            await ctx.reply(f"引数が足りないか多いです。\n`{PREFIX}ss sort [サーバーID1] [サーバーID2]`")
            return
        try:
            args[2] = int(args[2])
            args[3] = int(args[3])
        except ValueError:
            await ctx.reply("サーバーIDの欄には数値が入ります。")
            return
        if args[2] > int(n_fc.steam_server_list[ctx.guild.id]["value"]) or args[3] > int(n_fc.steam_server_list[ctx.guild.id]["value"]):
            await ctx.reply(f"{ctx.guild.name}に登録されているサーバーの数は{n_fc.steam_server_list[ctx.guild.id]['value']}個です。\n無効なサーバーIDを指定しないでください。")
            return
        if args[2] <= 0 or args[3] <= 0:
            await ctx.reply(f"サーバーIDは1から順につけられます。\n無効なサーバーIDを指定しないでください。")
            return
        try:
            n_fc.steam_server_list[ctx.guild.id][f"{args[2]}_nm"], n_fc.steam_server_list[ctx.guild.id][f"{args[2]}_ad"], n_fc.steam_server_list[ctx.guild.id][f"{args[3]}_nm"], n_fc.steam_server_list[ctx.guild.id][f"{args[3]}_ad"] = n_fc.steam_server_list[ctx.guild.id][f"{args[3]}_nm"], n_fc.steam_server_list[ctx.guild.id][f"{args[3]}_ad"], n_fc.steam_server_list[ctx.guild.id][f"{args[2]}_nm"], n_fc.steam_server_list[ctx.guild.id][f"{args[2]}_ad"]
            await ctx.reply("入れ替えが完了しました。")
            return
        except BaseException as err:
            await ctx.reply(f"入れ替え中にエラーが発生しました。\n{err}")
            return


    elif args[1] == "del":
        if ctx.guild.id not in n_fc.steam_server_list:
            await ctx.message.reply("サーバーは登録されていません。")
            return
        if ctx.message.content != "n!ss del all":
            try:
                del_num = int(ctx.message.content[9:])
            except BaseException as err:
                await ctx.message.reply(embed=eh.eh(err))
                return
            if admin_check.admin_check(ctx.guild, ctx.message.author):
                if del_num > int(n_fc.steam_server_list[ctx.guild.id]["value"]):
                    await ctx.message.reply(embed=nextcord.Embed(title="エラー", description="そのサーバーは登録されていません！\n`n!ss list`で確認してみてください！", color=0xff0000))
                    return
                if del_num <= 0:
                    await ctx.message.reply(embed=nextcord.Embed(title="エラー", description="リストで0以下のナンバーは振り当てられていません。", color=0xff0000))
                    return
                try:
                    all_value = int(n_fc.steam_server_list[ctx.guild.id]["value"])
                    print(all_value)
                    for i in range(all_value - del_num):
                        print(i)
                        n_fc.steam_server_list[ctx.guild.id][f"{del_num + i - 1}_nm"] = n_fc.steam_server_list[ctx.guild.id][f"{del_num + i}_nm"]
                        n_fc.steam_server_list[ctx.guild.id][f"{del_num + i - 1}_ad"] = n_fc.steam_server_list[ctx.guild.id][f"{del_num + i}_ad"]
                    del n_fc.steam_server_list[ctx.guild.id][f"{all_value}_nm"]
                    del n_fc.steam_server_list[ctx.guild.id][f"{all_value}_ad"]
                    n_fc.steam_server_list[ctx.guild.id]["value"] = all_value - 1
                    await ctx.message.reply(embed=nextcord.Embed(title="削除", description=f"ID:{del_num}のサーバーをリストから削除しました。", color=0xff0000))   
                except BaseException as err:
                    print(err)
                    await ctx.message.reply(embed=eh.eh(err))
                    return
            else:
                await ctx.message.reply(embed=nextcord.Embed(title="エラー", description="管理者権限がありません。", color=0xff0000))
                return
        else:
            def check(m):
                return (m.content == 'y' or m.content == 'n') and m.author == ctx.author and m.channel == ctx.channel
            del_re = await ctx.reply("サーバーリストを削除してもよろしいですか？\n削除するには`y`、キャンセルするには`n`と送信してください。\n(10秒以内)")
            try:
                msg = await self.bot.wait_for('message', check=check, timeout=10)
            except asyncio.TimeoutError:
                await del_re.edit(content="時間切れです...")
                return
            if msg.content == "n":
                await del_re.edit(content="分かりました。\nまた呼んでね...")
                return
            else:
                del n_fc.steam_server_list[ctx.guild.id]
                with open(f'{home_dir}/steam_server_list.nira', 'wb') as f:
                    pickle.dump(n_fc.steam_server_list, f)
                await del_re.edit(content=None,embed=nextcord.Embed(title="リスト削除", description=f"{ctx.author.mention}\nリストは正常に削除されました。", color=0xffffff))
                return
            return
        return
    
    elif args[1] == "all":
        if ctx.guild.id not in n_fc.steam_server_list:
            await ctx.message.reply("サーバーは登録されていません。")
            return
        async with ctx.channel.typing():
            embed = nextcord.Embed(title="Server Status Checker", description=f"{ctx.message.author.mention}\n:globe_with_meridians:Status\n==========", color=0x00ff00)
            for i in map(str, range(1, int(n_fc.steam_server_list[ctx.guild.id]["value"])+1)):
                await server_check.server_check_async(self.bot.loop, embed, 1, ctx.guild.id, i)
            await asyncio.sleep(1)
            await ctx.message.reply(embed=embed)
            return
    
    elif len(args) > 2:
        await ctx.reply(f"引数とか何かがおかしいです。\n\n{ss_commands}")
        return
    
    else:
        if ctx.guild.id not in n_fc.steam_server_list:
            await ctx.message.reply("サーバーは登録されていません。")
            return
        async with ctx.channel.typing():
            embed = nextcord.Embed(title="Server Status Checker", description=f"{ctx.message.author.mention}\n:globe_with_meridians:Status\n==========", color=0x00ff00)
            server_check.server_check(embed, 0, ctx.guild.id, args[1])
            await asyncio.sleep(1)
            await ctx.message.reply(embed=embed)
            return


class server_status(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot


    # AutoSS Force用のView
    class Reload_SS_Auto(nextcord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)

        @nextcord.ui.button(label='再読み込み', style=nextcord.ButtonStyle.green)
        async def reload(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
            try:
                status_message = n_fc.pid_ss[interaction.guild.id][1]
                n_fc.pid_ss[interaction.guild.id][0].cancel()
                n_fc.pid_ss[interaction.guild.id] = (asyncio.ensure_future(ss_force(asyncio.get_event_loop(), status_message)), status_message)
                await interaction.response.send_message('Reloaded!', ephemeral=True)
                logging.info("reloaded")

            except BaseException as err:
                await interaction.response.send_message(f'エラーが発生しました。\n{err}', ephemeral=True)
                logging.error(err)


    # SS再チェック用のView
    class Recheck_SS_Embed(nextcord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)

        @nextcord.ui.button(label='もう一度チェックする', style=nextcord.ButtonStyle.green)
        async def recheck(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
            try:
                embed = nextcord.Embed(title="Server Status Checker", description=f":globe_with_meridians:Status\n==========", color=0x00ff00)
                for i in map(str, range(1, int(n_fc.steam_server_list[interaction.guild.id]["value"])+1)):
                    await server_check.server_check_async(asyncio.get_event_loop(), embed, 0, interaction.guild.id, i)
                await interaction.response.send_message('ServerCheck', embed=embed, view=server_status.Recheck_SS_Embed())
                logging.info("rechecked")
                
            except BaseException as err:
                await interaction.response.send_message(f"エラーが発生しました。\n{err}", ephemeral=True)
                logging.err(err)


    @commands.command(name="ss",help="""\
Steam非公式サーバーのステータスを表示します
このコマンドは、**user毎**で**10秒**のクールダウンがあります。
このコマンドのヘルプは別ページにあります。
[ヘルプはこちら](https://sites.google.com/view/nira-bot/%E3%82%B3%E3%83%9E%E3%83%B3%E3%83%89/ss)""")
    @commands.cooldown(1, 10, type=commands.BucketType.user)
    async def ss(self, ctx: commands.Context):
        await ss_base(self, ctx)


    @nextcord.slash_command(name="ss", description="Show Steam Dedicated Server's status", guild_ids=n_fc.GUILD_IDS)
    async def ss_slash(self, interaction: Interaction):
        pass


    @ss_slash.subcommand(name="add", description="Steam非公式サーバーを追加します")
    async def add_slash(
            self,
            interaction: Interaction,
            ServerName: str = SlashOption(
                name="ServerName",
                description="オフライン時に表示されるサーバーの名前",
                required=True
            ),
            ServerAddress: str = SlashOption(
                name="ServerAddress",
                description="サーバーのIPアドレスまたはドメイン名",
                required=True
            ),
            ServerPort: int = SlashOption(
                name="ServerPort",
                description="サーバーのポート番号",
                required=True
            )
        ):
            await interaction.response.defer()
            try:
                if admin_check.admin_check(interaction.guild, interaction.user):
                    if interaction.guild.id not in n_fc.steam_server_list:
                        n_fc.steam_server_list[interaction.guild.id] = {"value": "0"}
                    SSValue = int(n_fc.steam_server_list[interaction.guild.id]["value"])
                    n_fc.steam_server_list[interaction.guild.id][f"{SSValue + 1}_ad"] = (ServerAddress, ServerPort)
                    n_fc.steam_server_list[interaction.guild.id][f"{SSValue + 1}_nm"] = ServerName
                    n_fc.steam_server_list[interaction.guild.id]["value"] = str(SSValue + 1)
                    with open(f'{home_dir}/steam_server_list.nira', 'wb') as f:
                        pickle.dump(n_fc.steam_server_list, f)
                    await interaction.followup.send(embed=nextcord.Embed(title="SteamDedicatedServer", description=f"サーバーの追加に成功しました。\サーバー名：`{ServerName}`\nサーバーアドレス: `{ServerAddress}:{ServerPort}`", color=0x00ff00), ephemeral=True)
                    return
                else:
                    await interaction.followup.send(embed=nextcord.Embed(title="SteamDedicatedServer", description="管理者権限がありません。", color=0xff0000), ephemeral=True)
                    return
            except BaseException as err:
                await interaction.followup.send(f"サーバー追加時にエラーが発生しました。\n```sh\n{err}```", ephemeral=True)
                return


    @ss_slash.subcommand(name="del", description="Steam非公式サーバーを削除します")
    async def del_slash(
            self,
            interaction: Interaction,
            ServerID: int = SlashOption(
                name="ServerID",
                description="削除するサーバーのID",
                required=True
            )
        ):
            await interaction.response.defer()
            try:
                if admin_check.admin_check(interaction.guild, interaction.user):
                    if interaction.guild.id not in n_fc.steam_server_list:
                        await interaction.followup.send(embed=nextcord.Embed(title="SteamDedicatedServer", description="このサーバーにはSteam Dedicated Serverは追加されていません。", color=0xff0000), ephemeral=True)
                        return
                    if f"{ServerID}_ad" not in n_fc.steam_server_list[interaction.guild.id]:
                        await interaction.followup.send(embed=nextcord.Embed(title="SteamDedicatedServer", description="指定されたIDのサーバーは存在しません。", color=0xff0000), ephemeral=True)
                        return
                    del n_fc.steam_server_list[interaction.guild.id][f"{ServerID}_nm"]
                    del n_fc.steam_server_list[interaction.guild.id][f"{ServerID}_ad"]
                    with open(f'{home_dir}/steam_server_list.nira', 'wb') as f:
                        pickle.dump(n_fc.steam_server_list, f)
                    await interaction.followup.send(embed=nextcord.Embed(title="SteamDedicatedServer", description=f"サーバーの削除に成功しました。", color=0x00ff00), ephemeral=True)
                    return
                else:
                    await interaction.followup.send(embed=nextcord.Embed(title="SteamDedicatedServer", description="管理者権限がありません。", color=0xff0000), ephemeral=True)
                    return
            except BaseException as err:
                await interaction.followup.send(f"サーバー削除時にエラーが発生しました。\n```sh\n{err}```", ephemeral=True)
                return


    @ss_slash.subcommand(name="list", description="Steam非公式サーバーの一覧を表示します")
    async def list_slash(self, interaction: Interaction):
        await interaction.response.defer()
        try:
            if admin_check.admin_check(interaction.guild, interaction.user):
                if interaction.guild.id not in n_fc.steam_server_list:
                    await interaction.followup.send(embed=nextcord.Embed(title="SteamDedicatedServer", description="このサーバーにはSteam Dedicated Serverは追加されていません。", color=0xff0000), ephemeral=True)
                    return
                SSValue = int(n_fc.steam_server_list[interaction.guild.id]["value"])
                if SSValue == 0:
                    await interaction.followup.send(embed=nextcord.Embed(title="SteamDedicatedServer", description="Steam Dedicated Serverは追加されていません。", color=0xff0000), ephemeral=True)
                    return
                embed = nextcord.Embed(title="SteamDedicatedServer", description=f"{interaction.guild.name}", color=0x00ff00)
                for i in range(1, SSValue + 1):
                    embed.add_field(name=f"{i}番目のサーバー", value=f"サーバー名：`{n_fc.steam_server_list[interaction.guild.id][f'{i}_nm']}`\nサーバーアドレス：`{n_fc.steam_server_list[interaction.guild.id][f'{i}_ad'][0]}:{n_fc.steam_server_list[interaction.guild.id][f'{i}_ad'][1]}`", inline=False)
                await interaction.user.send(embed=embed)
                await interaction.followup.send("Sended!", ephemeral=True)
                return
            else:
                await interaction.followup.send(embed=nextcord.Embed(title="SteamDedicatedServer", description="管理者権限がありません。", color=0xff0000), ephemeral=True)
                return
        except BaseException as err:
            await interaction.followup.send(f"サーバー一覧表示時にエラーが発生しました。\n```sh\n{err}```", ephemeral=True)
            return


    @ss_slash.subcommand(name="sort", description="Steam非公式サーバーの一覧をソートします")
    async def sort_slash(
            self,
            interaction: Interaction,
            SortSource: int = SlashOption(
                name="SortSource",
                description="置き換え元のサーバーID",
                required=True
            ),
            SortDestination: int = SlashOption(
                name="SortDestination",
                description="置き換え先のサーバーID",
                required=True
            )
        ):
        await interaction.response.defer()
        try:
            if admin_check.admin_check(interaction.guild, interaction.user):
                if interaction.guild.id not in n_fc.steam_server_list:
                    await interaction.followup.send(embed=nextcord.Embed(title="SteamDedicatedServer", description="このサーバーにはSteam Dedicated Serverは追加されていません。", color=0xff0000), ephemeral=True)
                    return
                SSValue = int(n_fc.steam_server_list[interaction.guild.id]["value"])
                if SSValue == 0:
                    await interaction.followup.send(embed=nextcord.Embed(title="SteamDedicatedServer", description="Steam Dedicated Serverは追加されていません。", color=0xff0000), ephemeral=True)
                    return
                if SortSource > SSValue or SortDestination > SSValue:
                    await interaction.followup.send(embed=nextcord.Embed(title="SteamDedicatedServer", description="指定されたIDのサーバーは存在しません。", color=0xff0000), ephemeral=True)
                    return
                if SortSource == SortDestination:
                    await interaction.followup.send(embed=nextcord.Embed(title="SteamDedicatedServer", description="置き換え元と置き換え先が同じです。", color=0xff0000), ephemeral=True)
                    return
                if SortSource <= 0 or SortDestination <= 0:
                    await interaction.followup.send(embed=nextcord.Embed(title="SteamDedicatedServer", description="指定したIDは不正です。", color=0xff0000), ephemeral=True)
                    return
                n_fc.steam_server_list[interaction.guild.id][f"{SortSource}_nm"], n_fc.steam_server_list[interaction.guild.id][f"{SortSource}_ad"], n_fc.steam_server_list[interaction.guild.id][f"{SortDestination}_nm"], n_fc.steam_server_list[interaction.guild.id][f"{SortDestination}_ad"] = n_fc.steam_server_list[interaction.guild.id][f"{SortDestination}_nm"], n_fc.steam_server_list[interaction.guild.id][f"{SortDestination}_ad"], n_fc.steam_server_list[interaction.guild.id][f"{SortSource}_nm"], n_fc.steam_server_list[interaction.guild.id][f"{SortSource}_ad"]
                await interaction.followup.send("ソートが完了しました。", ephemeral=True)
                return
            else:
                await interaction.followup.send(embed=nextcord.Embed(title="SteamDedicatedServer", description="管理者権限がありません。", color=0xff0000), ephemeral=True)
                return
        except BaseException as err:
            await interaction.followup.send(f"ソート時にエラーが発生しました。\n```sh\n{err}```", ephemeral=True)
            return


    @ss_slash.subcommand(name="edit", description="Steam非公式サーバーの一覧を編集します")
    async def edit_slash(
            self,
            interaction: Interaction,
            EditSource: int = SlashOption(
                name="EditSource",
                description="置き換え元のサーバーID",
                required=True
            ),
            ServerName: str = SlashOption(
                name="ServerName",
                description="サーバー名",
                required=True
            ),
            ServerAddress: str = SlashOption(
                name="ServerAddress",
                description="サーバーアドレス",
                required=True
            ),
            ServerPort: int = SlashOption(
                name="ServerPort",
                description="サーバーポート",
                required=True
            )
        ):
        await interaction.response.defer()
        try:
            if admin_check.admin_check(interaction.guild, interaction.user):
                if interaction.guild.id not in n_fc.steam_server_list:
                    await interaction.followup.send(embed=nextcord.Embed(title="SteamDedicatedServer", description="このサーバーにはSteam Dedicated Serverは追加されていません。", color=0xff0000), ephemeral=True)
                    return
                SSValue = int(n_fc.steam_server_list[interaction.guild.id]["value"])
                if SSValue == 0:
                    await interaction.followup.send(embed=nextcord.Embed(title="SteamDedicatedServer", description="Steam Dedicated Serverは追加されていません。", color=0xff0000), ephemeral=True)
                    return
                if EditSource > SSValue:
                    await interaction.followup.send(embed=nextcord.Embed(title="SteamDedicatedServer", description="指定されたIDのサーバーは存在しません。", color=0xff0000), ephemeral=True)
                    return
                if EditSource <= 0:
                    await interaction.followup.send(embed=nextcord.Embed(title="SteamDedicatedServer", description="指定したIDは不正です。", color=0xff0000), ephemeral=True)
                    return
                n_fc.steam_server_list[interaction.guild.id][f"{EditSource}_nm"] = ServerName
                n_fc.steam_server_list[interaction.guild.id][f"{EditSource}_ad"] = (ServerAddress, ServerPort)
                await interaction.followup.send("編集が完了しました。", ephemeral=True)
            else:
                await interaction.followup.send(embed=nextcord.Embed(title="SteamDedicatedServer", description="管理者権限がありません。", color=0xff0000), ephemeral=True)
                return
        except BaseException as err:
            await interaction.followup.send(f"編集時にエラーが発生しました。\n```sh\n{err}```", ephemeral=True)
            return


    @ss_slash.subcommand(name="auto", description="Get Steam Dedicated Server's status automatically.")
    async def auto_slash(self, interaction: Interaction):
        pass


    @auto_slash.subcommand(name="on", description="鯖が落ちたと思われる際に通知する")
    async def auto_on_slash(
            self,
            interaction: Interaction,
            mentionUser: nextcord.User = SlashOption(
                name="mentionUser",
                description="メンションするユーザー",
                required=True
            )
        ):
            await interaction.response.defer()
            try:
                if interaction.guild.id not in n_fc.steam_server_list:
                    await interaction.followup.send("サーバーが登録されていません。", ephemeral=True)
                    return

                ment_id = str(mentionUser.id)
                mes_ss = await interaction.followup.send(f"Starting process...")

                if interaction.guild.id in n_fc.pid_ss:
                    await mes_ss.edit(content=f"既に{interaction.guild.name}でタスクが実行されています。")
                    return

                n_fc.pid_ss[interaction.guild.id] = (self.bot.loop.create_task(ss_loop_goes(self, ment_id, mes_ss)), mes_ss)
                return
            except BaseException as err:
                await interaction.followup.send(embed=eh.eh(err), ephemeral=True)
                return


    @auto_slash.subcommand(name="off", description="鯖が落ちたと思われる際に通知しないようにする")
    async def auto_off_slash(
            self,
            interaction: Interaction
        ):
        await interaction.response.defer()
        if interaction.guild.id not in n_fc.pid_ss:
            await interaction.followup.send("既に無効になっているか、コマンドが実行されていません。", ephemeral=True)
            return
        try:
            if n_fc.pid_ss[interaction.guild.id][0].done() == False or interaction.guild.id in n_fc.pid_ss:
                n_fc.pid_ss[interaction.guild.id][0].cancel()
                del n_fc.pid_ss[interaction.guild.id]
                del n_fc.force_ss_list[interaction.guild.id]
                await interaction.followup.send("AutoSSを無効にしました。", ephemeral=True)
                return
            else:
                await interaction.followup.send("既に無効になっているか、コマンドが実行されていません。", ephemeral=True)
        except BaseException as err:
            await interaction.followup.send(embed=eh.eh(err), ephemeral=True)
            return


    @auto_slash.subcommand(name="force", description="ずっと更新する鯖ステ表示を送信します")
    async def auto_force_slash(
            self,
            interaction: Interaction,
            ForceSSChannelID: int = SlashOption(
                name="ForceSSChannelID",
                description="（復元する場合のみ）チャンネルID",
                required=False
            ),
            ForceSSMessageID: int = SlashOption(
                name="ForceSSMessageID",
                description="（復元する場合のみ）メッセージID",
                required=False
            )
        ):
            await interaction.response.defer()
            if interaction.guild.id in n_fc.pid_ss:
                await interaction.followup.send(f"既に{interaction.guild.name}で他のAutoSSタスクが実行されています。", ephemeral=True)
                return
            if interaction.guild.id not in n_fc.steam_server_list:
                await interaction.followup.send("サーバーが登録されていません。", ephemeral=True)
                return
            mes_ss = await interaction.channel.send(f"Check your set message!")
            if interaction.guild.id in n_fc.pid_ss:
                await mes_ss.edit(content=f"既に{interaction.guild.name}でタスクが実行されています。", ephemeral=True)
                return
            if ForceSSChannelID is not None and ForceSSMessageID is not None:
                n_fc.force_ss_list[interaction.guild.id] = [interaction.channel.id, mes_ss.id]
                n_fc.pid_ss[interaction.guild.id] = (self.bot.loop.create_task(ss_force(asyncio.get_event_loop(), mes_ss)),mes_ss)
                return
            else:
                try:
                    messs = await get_mes(self.bot, ForceSSChannelID, ForceSSMessageID)
                except BaseException as err:
                    logging.error(err)
                    await interaction.followup.send("メッセージが見つかりませんでした。", ephemeral=True)
                    return
                await messs.edit(content="現在変更をしています...")
                n_fc.force_ss_list[interaction.guild.id] = [ForceSSChannelID, ForceSSMessageID]
                n_fc.pid_ss[interaction.guild.id] = (self.bot.loop.create_task(ss_force(asyncio.get_event_loop(), messs)),messs)
                return


    @ss_slash.subcommand(name="status", description="Steam非公式サーバーのステータスを表示します")
    async def status_slash(
            self,
            interaction: Interaction,
            ServerID: str = SlashOption(
                name="ServerID",
                description="デフォルトは空白。特定のサーバーだけ指定したい場合はIDを入力してください。又はallで詳細に表示します。",
                required=False
            )
        ):
        await interaction.response.defer()

        try:
            if ServerID == "all":
                if interaction.guild.id not in n_fc.steam_server_list:
                    await interaction.followup.send("サーバーは登録されていません。", ephemeral=True)
                    return
                embed = nextcord.Embed(title="Server Status Checker", description=f"{interaction.user.mention}\n:globe_with_meridians:Status\n==========", color=0x00ff00)
                for i in map(str, range(1, int(n_fc.steam_server_list[interaction.guild.id]["value"])+1)):
                    await server_check.server_check_async(self.bot.loop, embed, 1, interaction.guild.id, i)
                await interaction.followup.send(embed=embed)
                return

            elif ServerID != "":
                if interaction.guild.id not in n_fc.steam_server_list:
                    await interaction.followup.send("サーバーは登録されていません。", ephemeral=True)
                    return
                embed = nextcord.Embed(title="Server Status Checker", description=f"{interaction.user.mention}\n:globe_with_meridians:Status\n==========", color=0x00ff00)
                server_check.server_check(embed, 0, interaction.guild.id, ServerID)
                await interaction.followup.send(embed=embed)
                return

            else:
                if interaction.guild.id not in n_fc.steam_server_list:
                    await interaction.followup.send("サーバーは登録されていません。", ephemeral=True)
                    return
                embed = nextcord.Embed(title="Server Status Checker", description=f"{interaction.user.mention}\n:globe_with_meridians:Status\n==========", color=0x00ff00)
                for i in map(str, range(1, int(n_fc.steam_server_list[interaction.guild.id]["value"])+1)):
                    await server_check.server_check_async(self.bot.loop, embed, 0, interaction.guild.id, i)
                await interaction.followup.send(embed=embed, view=server_status.Recheck_SS_Embed())
                return

        except BaseException as err:
            await interaction.followup.send(f"ステータス取得時にエラーが発生しました。\n```sh\n{err}```", ephemeral=True)
            return



def setup(bot):
    bot.add_cog(server_status(bot))
    #importlib.reload(server_check)


