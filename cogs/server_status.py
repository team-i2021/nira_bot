import datetime
import pickle
import sys
from re import I

import discord
from discord.ext import commands

from cogs.embed import embed

#pingを送信するだけ

sys.path.append('../')
import asyncio
import datetime
import importlib
#loggingの設定
import logging
import os
import re
import subprocess
from multiprocessing import Array, Process
from subprocess import PIPE

import util.srtr as srtr
dir = sys.path[0]
from util import admin_check, eh, n_fc, server_check


class NoTokenLogFilter(logging.Filter):
    def filter(self, record):
        message = record.getMessage()
        return 'token' not in message

logger = logging.getLogger(__name__)
logger.addFilter(NoTokenLogFilter())
formatter = '%(asctime)s$%(filename)s$%(lineno)d$%(funcName)s$%(levelname)s:%(message)s'
logging.basicConfig(format=formatter, filename=f'{dir}/nira.log', level=logging.INFO)

ss_check_result = {}


async def ss_pin(self, ment_id, message):
    ss_check_result[message.guild.id] = {}
    await message.edit(content=f"チェックシステムを有効化しています...")
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
    if ctx.message.content == "n!ss reload":
        if ctx.message.author.id not in n_fc.py_admin:
            return
        try:
            importlib.reload(server_check)
            await ctx.reply("Reloaded.")
            return
        except BaseException as err:
            await ctx.reply(err)
            return
    if ctx.message.content[:8] == "n!ss add":
        if ctx.message.content == "n!ss add":
            await ctx.message.reply("構文が異なります。\n```n!ss add [表示名] [IPアドレス],[ポート番号]```")
            return
        try:
            if ctx.message.guild.id not in n_fc.steam_server_list:
                n_fc.steam_server_list[ctx.message.guild.id] = {"value": "0"}
            ad = ctx.message.content[9:].split(" ", 1)
            ad_name = str(ad[0])
            ad = re.sub("[^0-9a-zA-Z._-]", "", ad[1].split(",", 1))
            ad_port = int(ad[1])
            ad_ip = str(ad[0])
            sset_point = int(n_fc.steam_server_list[ctx.message.guild.id]["value"])
            n_fc.steam_server_list[ctx.message.guild.id][f"{sset_point + 1}_ad"] = (ad_ip, ad_port)
            n_fc.steam_server_list[ctx.message.guild.id][f"{sset_point + 1}_nm"] = ad_name
            n_fc.steam_server_list[ctx.message.guild.id]["value"] = str(sset_point + 1)
            await ctx.message.reply(f"サーバー名：{ad_name}\nサーバーアドレス：({ad_ip},{ad_port})")
            with open('/home/nattyantv/nira_bot_rewrite/steam_server_list.nira', 'wb') as f:
                pickle.dump(n_fc.steam_server_list, f)
            return
        except BaseException as err:
            await ctx.message.reply(embed=eh.eh(err))
    if ctx.message.content[:9] == "n!ss list":
        if ctx.message.guild.id not in n_fc.steam_server_list:
            await ctx.message.reply("サーバーは登録されていません。")
            return
        else:
            if admin_check.admin_check(ctx.message.guild, ctx.message.author) or ctx.message.author.id in n_fc.py_admin:
                user = await self.bot.fetch_user(ctx.message.author.id)
                embed = discord.Embed(title="Steam Server List", description=f"「{ctx.message.guild.name}」のサーバーリスト\n```保存数：{str(n_fc.steam_server_list[ctx.message.guild.id]['value'])}```", color=0x00ff00)
                for i in range(int(n_fc.steam_server_list[ctx.message.guild.id]['value'])):
                    embed.add_field(name=f"保存名：`{str(n_fc.steam_server_list[ctx.message.guild.id][f'{i+1}_nm'])}`", value=f"アドレス：`{str(n_fc.steam_server_list[ctx.message.guild.id][f'{i+1}_ad'])}`")
                await user.send(embed=embed)
                await ctx.message.add_reaction("\U00002705")
                return
            else:
                await ctx.message.reply(embed=discord.Embed(title="エラー", description="管理者権限がありません。", color=0xff0000))
                return
    if ctx.message.content[:9] == "n!ss auto":
        if admin_check.admin_check(ctx.message.guild, ctx.message.author) == False:
            await ctx.message.reply(embed=discord.Embed(title="エラー", description="管理者権限がありません。", color=0xff0000))
            return
        if ctx.message.content == "n!ss auto":
            await ctx.reply(embed=discord.Embed(title="エラー", description="引数が足りません。\n`n!ss auto on/off`"))
            return
        elif ctx.message.content[10:12] == "on":
            try:
                if ctx.message.guild.id not in n_fc.steam_server_list:
                    await ctx.reply("サーバーが存在しません。")
                    return
                if len(ctx.message.content) <= 13:
                    ment_id = ctx.message.author.id
                else:
                    ment_id = str("".join(re.findall(r'[0-9]', ctx.message.content[13:])))
                    if ment_id == "":
                        await ctx.reply("ユーザーIDが不正です。\n`n!ss auto on [UserID]`")
                        return
                mes_ss = await ctx.message.channel.send(f"Starting process...")
                if ctx.message.guild.id in n_fc.pid_ss:
                    await mes_ss.edit(content=f"既に{ctx.message.guild.name}でタスクが実行されています。")
                    return
                n_fc.pid_ss[ctx.message.guild.id] = self.bot.loop.create_task(ss_loop_goes(self, ment_id, mes_ss))
                return
            except BaseException as err:
                await ctx.reply(embed=eh.eh(err))
                return
        elif ctx.message.content[10:13] == "off":
            if ctx.message.guild.id not in n_fc.pid_ss:
                await ctx.reply("既に無効になっているか、コマンドが実行されていません。")
            try:
                if n_fc.pid_ss[ctx.message.guild.id].done() == False:
                    n_fc.pid_ss[ctx.message.guild.id].cancel()
                    del n_fc.pid_ss[ctx.message.guild.id]
                    await ctx.reply("AutoSSを無効にしました。")
                    return
                else:
                    await ctx.reply("既に無効になっているか、コマンドが実行されていません。")
            except BaseException as err:
                await ctx.reply(embed=eh.eh(err))
                return
        else:
            if ctx.message.guild.id not in n_fc.pid_ss:
                await ctx.reply("`n!ss auto [on/off]`\nAutoSSは無効になっています。")
                return
            try:
                if n_fc.pid_ss[ctx.message.guild.id].done() == True:
                    await ctx.reply("`n!ss auto [on/off]`\nAutoSSは無効になっています。")
                else:
                    await ctx.reply("`n!ss auto [on/off]`\nAutoSSは有効になっています。")
            except BaseException as err:
                await ctx.reply(embed=eh.eh(err))
                return
        return
    if ctx.message.content[:9] == "n!ss edit":
        if ctx.message.content == "n!ss edit":
            await ctx.message.reply("構文が異なります。\n```n!ss edit [サーバーナンバー] [名前] [IPアドレス],[ポート番号]```")
            return
        if ctx.message.guild.id not in n_fc.steam_server_list:
            await ctx.message.reply("サーバーは登録されていません。")
            return
        adre = ctx.message.content[10:].split(" ", 3)
        s_id = int("".join(re.findall(r'[0-9]', adre[0])))
        s_nm = str(adre[1])
        s_adre = str(adre[2]).split(",", 2)
        s_port = int(s_adre[1])
        s_ip = str("".join(re.findall(r'[0-9]|\.', s_adre[0])))
        b_value = int(n_fc.steam_server_list[ctx.message.guild.id]["value"])
        if b_value < s_id:
            await ctx.message.reply("そのサーバーナンバーのサーバーは登録されていません！\n`n!ss list`で確認してみてください。")
            return
        try:
            n_fc.steam_server_list[ctx.message.guild.id][f"{s_id}_ad"] = (s_ip, s_port)
            n_fc.steam_server_list[ctx.message.guild.id][f"{s_id}_nm"] = s_nm
            await ctx.message.reply(f"サーバーナンバー：{s_id}\nサーバー名：{s_nm}\nサーバーアドレス：{s_ip},{s_port}")
            with open('/home/nattyantv/nira_bot_rewrite/steam_server_list.nira', 'wb') as f:
                pickle.dump(n_fc.steam_server_list, f)
            return
        except BaseException as err:
            await ctx.message.reply(embed=eh.eh(err))
            return
    if ctx.message.content[:8] == "n!ss del":
        if ctx.message.guild.id not in n_fc.steam_server_list:
            await ctx.message.reply("サーバーは登録されていません。")
            return
        if ctx.message.content != "n!ss del all":
            try:
                del_num = int(ctx.message.content[9:])
            except BaseException as err:
                await ctx.message.reply(embed=eh.eh(err))
                return
            if admin_check.admin_check(ctx.message.guild, ctx.message.author):
                if del_num > int(n_fc.steam_server_list[ctx.message.guild.id]["value"]):
                    await ctx.message.reply(embed=discord.Embed(title="エラー", description="そのサーバーは登録されていません！\n`n!ss list`で確認してみてください！", color=0xff0000))
                    return
                if del_num <= 0:
                    await ctx.message.reply(embed=discord.Embed(title="エラー", description="リストで0以下のナンバーは振り当てられていません。", color=0xff0000))
                    return
                try:
                    all_value = int(n_fc.steam_server_list[ctx.message.guild.id]["value"])
                    print(all_value)
                    for i in range(all_value - del_num):
                        print(i)
                        n_fc.steam_server_list[ctx.message.guild.id][f"{del_num + i - 1}_nm"] = n_fc.steam_server_list[ctx.message.guild.id][f"{del_num + i}_nm"]
                        n_fc.steam_server_list[ctx.message.guild.id][f"{del_num + i - 1}_ad"] = n_fc.steam_server_list[ctx.message.guild.id][f"{del_num + i}_ad"]
                    del n_fc.steam_server_list[ctx.message.guild.id][f"{all_value}_nm"]
                    del n_fc.steam_server_list[ctx.message.guild.id][f"{all_value}_ad"]
                    n_fc.steam_server_list[ctx.message.guild.id]["value"] = all_value - 1
                    await ctx.message.reply(embed=discord.Embed(title="削除", description=f"ID:{del_num}のサーバーをリストから削除しました。", color=0xff0000))   
                except BaseException as err:
                    print(err)
                    await ctx.message.reply(embed=eh.eh(err))
                    return
            else:
                await ctx.message.reply(embed=discord.Embed(title="エラー", description="管理者権限がありません。", color=0xff0000))
                return
        else:
            del_re = await ctx.reply("サーバーリストを削除しますか？リスト削除には管理者権限が必要です。\n\n:o:：削除\n:x:：キャンセル")
            await del_re.add_reaction("\U00002B55")
            await del_re.add_reaction("\U0000274C")
            return
        return
    print(datetime.datetime.now())
    if ctx.message.content == "n!ss":
        if ctx.message.guild.id not in n_fc.steam_server_list:
            await ctx.message.reply("サーバーは登録されていません。")
            return
        async with ctx.message.channel.typing():
            embed = discord.Embed(title="Server Status Checker", description=f"{ctx.message.author.mention}\n:globe_with_meridians:Status\n==========", color=0x00ff00)
            for i in map(str, range(1, int(n_fc.steam_server_list[ctx.message.guild.id]["value"])+1)):
                await server_check.server_check_async(self.bot.loop, embed, 0, ctx.message.guild.id, i)
            await asyncio.sleep(1)
            await ctx.message.reply(embed=embed)
        return
    mes = ctx.message.content
    try:
        mes_te = mes.split(" ", 1)[1]
    except BaseException as err:
        await ctx.message.reply(embed=eh.eh(err))
        return
    if mes_te != "all":
        if ctx.message.guild.id not in n_fc.steam_server_list:
            await ctx.message.reply("サーバーは登録されていません。")
            return
        async with ctx.message.channel.typing():
            embed = discord.Embed(title="Server Status Checker", description=f"{ctx.message.author.mention}\n:globe_with_meridians:Status\n==========", color=0x00ff00)
            server_check.server_check(embed, 0, ctx.message.guild.id, mes_te)
            await asyncio.sleep(1)
            await ctx.message.reply(embed=embed)
            return
    elif mes_te == "all":
        if ctx.message.guild.id not in n_fc.steam_server_list:
            await ctx.message.reply("サーバーは登録されていません。")
            return
        async with ctx.message.channel.typing():
            embed = discord.Embed(title="Server Status Checker", description=f"{ctx.message.author.mention}\n:globe_with_meridians:Status\n==========", color=0x00ff00)
            for i in map(str, range(1, int(n_fc.steam_server_list[ctx.message.guild.id]["value"])+1)):
                await server_check.server_check_async(self.bot.loop, embed, 1, ctx.message.guild.id, i)
            await asyncio.sleep(1)
            await ctx.message.reply(embed=embed)
            return
    return


class server_status(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    @commands.cooldown(1, 10, type=commands.BucketType.guild)
    async def ss(self, ctx: commands.Context):
        await ss_base(self, ctx)


def setup(bot):
    bot.add_cog(server_status(bot))
