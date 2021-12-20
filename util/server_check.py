# coding: utf-8
from util import n_fc
import asyncio
import util.web_api as web_api
import a2s
import datetime
import sys
import math


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

# 主にサーバーステータスを取得するコード


async def server_check_loop(loop, g_id, n):
    return await loop.run_in_executor(
        None, ss_bool, g_id, n
    )


# ステータスチェック中にメッセージ返信ができないものを修正する(Created by tasuren)
async def server_check_async(loop, embed, type, g_id, n):
    return await loop.run_in_executor(
        None, server_check, embed, type, g_id, n
    )

# サーバーのステータスをチェックする
def server_check(embed, type, g_id, n):
    try:
        sv_ad = n_fc.steam_server_list[g_id][f"{n}_ad"]
        sv_nm = n_fc.steam_server_list[g_id][f"{n}_nm"]
    except BaseException:
        embed.add_field(name=f"サーバーは{n}にはセットされていません。", value="`n!ss list`でサーバーリストを確認してみましょう！", inline=False)
        return
    sv_dt = "None"
    try:
        if web_api.server_status(sv_ad[0], sv_ad[1]) == False:
            if type == 0:
                embed.add_field(name=f"> {sv_nm}", value=":ng:オフライン\n==========", inline=False)
            if type == 1:
                embed.add_field(name=f"> {sv_nm}", value=f"```Steam WEB APIでサーバーが認識されていません。```", inline=False)
            return True
        sv_dt = a2s.info(sv_ad)
        if type == 0:
            embed.add_field(name=f"> {sv_dt.server_name} - {sv_dt.map_name}", value=":white_check_mark:オンライン", inline=False)
        elif type == 1:
            embed.add_field(name=f"> {sv_dt.server_name} - {sv_dt.map_name}", value=f"```{sv_dt}```", inline=False)
        user = ""
        sv_us = a2s.players(sv_ad)
        if type == 0:
            if sv_us != []:
                for i in range(len(sv_us)):
                    user_add = str(sv_us[i].name)
                    user_time = int(sv_us[i].duration/60)
                    if user_time >= 60:
                        user_time = f"{int(user_time // 60)}時間{int(user_time % 60)}"
                    if user_add != "":
                        user = user + "\n" + f"```{user_add} | {user_time}分```"
                if user == "":
                    user = "（ユーザーデータが取得出来ませんでした。）"
                embed.add_field(name="> Online User", value=f"プレーヤー数:{len(sv_us)}人{user}\n==========", inline=False)
            else:
                embed.add_field(name="> Online User", value=":information_source:オンラインユーザーはいません。\n==========", inline=False)
        elif type == 1:
            embed.add_field(name="> Online User", value=f"```{sv_us}```", inline=False)
    except BaseException as err:
        if str(err) == "timed out":
            if type == 0:
                embed.add_field(name=f"> {sv_nm}", value=":ng:サーバーに接続できませんでした。(タイムアウト)\n==========", inline=False)
            if type == 1:
                embed.add_field(name=f"> {sv_nm}", value=f"```{err}```", inline=False)
        else:
            logging.error(f"an error has occured during ServerStatus checking\n{err}")
            if type == 0:
                embed.add_field(name=f"> {sv_nm}", value=":x:不明なエラーが発生しました。\n==========", inline=False)
            if type == 1:
                embed.add_field(name=f"> {sv_nm}", value=f"```{err}```", inline=False)
    return True

#Bool返すタイプ
def ss_bool(g_id, n):
    sv_ad = n_fc.steam_server_list[g_id][f"{n}_ad"]
    for _ in range(3):
        try:
            if web_api.server_status(sv_ad[0], sv_ad[1]) == False:
                continue
            a2s.info(sv_ad)
            a2s.players(sv_ad)
        except BaseException:
            pass
        else:
            return True
    else:
        return False

#embed
# サーバーのステータスをチェックする
def ss_pin_embed(embed, g_id, n):
    sv_ad = n_fc.steam_server_list[g_id][f"{n}_ad"]
    sv_nm = n_fc.steam_server_list[g_id][f"{n}_nm"]
    sv_dt = "None"
    try:
        if web_api.server_status(sv_ad[0], sv_ad[1]) == False:
            embed.add_field(name=f"> {sv_nm}", value=":ng:オフライン\n==========", inline=False)
            return
        sv_dt = a2s.info(sv_ad)
        embed.add_field(name=f"> {sv_dt.server_name} - {sv_dt.map_name}", value=":white_check_mark:オンライン", inline=False)
        user = ""
        sv_us = a2s.players(sv_ad)
        if type == 0:
            if sv_us != []:
                for i in range(len(sv_us)):
                    user_add = str(sv_us[i].name)
                    user_time = int(sv_us[i].duration/60)
                    if user_time >= 60:
                        user_time = f"{int(user_time // 60)}時間{int(user_time % 60)}"
                    if user_add != "":
                        user = user + "\n" + f"```{user_add} | {user_time}分```"
                if user == "":
                    user = "（ユーザーデータが取得出来ませんでした。）"
                embed.add_field(name="> Online User", value=f"プレーヤー数:{len(sv_us)}人{user}\n==========", inline=False)
            else:
                embed.add_field(name="> Online User", value=":information_source:オンラインユーザーはいません。\n==========", inline=False)
        elif type == 1:
            embed.add_field(name="> Online User", value=f"```{sv_us}```", inline=False)
    except BaseException as err:
        if str(err) == "timed out":
            if type == 0:
                embed.add_field(name=f"> {sv_nm}", value=":ng:サーバーに接続できませんでした。(タイムアウト)\n==========", inline=False)
            if type == 1:
                embed.add_field(name=f"> {sv_nm}", value=f"```{err}```", inline=False)
        else:
            logging.error(f"an error has occured during ServerStatus checking\n{err}")
            if type == 0:
                embed.add_field(name=f"> {sv_nm}", value=":x:不明なエラーが発生しました。\n==========", inline=False)
            if type == 1:
                embed.add_field(name=f"> {sv_nm}", value=f"```{err}```", inline=False)
    return True
