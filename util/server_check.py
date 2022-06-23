# coding: utf-8
#from cogs.server_status import ss_pin
from util import n_fc
import asyncio
import util.web_api as web_api
import a2s
import datetime
import sys
import math
import re
import logging

# 主にサーバーステータスを取得するコード


def ip_check(address: str) -> bool:
    """\
指定したaddressがドメインか、IPアドレスかどうかを判定します。
（正確に言うと数字とピリオドだけであればTrue）"""
    if re.search("[^0-9.]", address):
        return False
    else:
        return True


async def ss_pin_async(loop, embed, g_id, n):
    return await loop.run_in_executor(
        None, ss_pin_embed, embed, g_id, n
    )


async def server_check_loop(loop, g_id, n):
    return await loop.run_in_executor(
        None, ss_bool, g_id, n
    )


# ステータスチェック中にメッセージ返信ができないものを修正する(Created by tasuren)
async def server_check_async(loop, embed, type, g_id, n):
    return await loop.run_in_executor(
        None, server_check, embed, type, g_id, n
    )


def RetryInfo(address, count: int) -> a2s.SourceInfo or None:
    """サーバーのステータスを取得しますが、その際`count`回リトライします。"""
    for _ in range(count):
        try:
            info = a2s.info(address)
            return info
        except BaseException:
            pass
    return None

# サーバーのステータスをチェックする


def server_check(embed, type, g_id, n):
    try:
        sv_ad = n_fc.steam_server_list[g_id][f"{n}_ad"]
        sv_nm = n_fc.steam_server_list[g_id][f"{n}_nm"]
    except BaseException:
        embed.add_field(name=f"サーバーは{n}にはセットされていません。",
                        value="`n!ss list`でサーバーリストを確認してみましょう！", inline=False)
        return
    sv_dt = "None"
    try:
        if ip_check(sv_ad[0]):
            if web_api.server_status(sv_ad[0], sv_ad[1]) == False:
                if type == 0:
                    embed.add_field(
                        name=f"> {sv_nm}", value=":ng:オフライン\n==========", inline=False)
                if type == 1:
                    embed.add_field(
                        name=f"> {sv_nm}", value=f"```Steam WEB APIでサーバーが認識されていません。```", inline=False)
                return True
        sv_dt = RetryInfo(sv_ad, 3)
        if sv_dt is None:
            raise TimeoutError("timed out")
        #sv_dt = a2s.info(sv_ad)
        if type == 0:
            embed.add_field(name=f"> {sv_dt.server_name} - {sv_dt.map_name}",
                            value=":white_check_mark:オンライン", inline=False)
        elif type == 1:
            embed.add_field(
                name=f"> {sv_dt.server_name} - {sv_dt.map_name}", value=f"```{sv_dt}```", inline=False)
        user = ""
        sv_us = a2s.players(sv_ad)
        us = 0
        if type == 0:
            if sv_us != []:
                for i in range(len(sv_us)):
                    user_add = str(sv_us[i].name)
                    user_time = int(sv_us[i].duration/60)
                    if user_time >= 60:
                        user_time = f"{int(user_time // 60)}時間{int(user_time % 60)}"
                    if user_add != "":
                        user = user + f"\n{user_add} | {user_time}分"
                    else:
                        us = us - 1
                if user != "":
                    embed.add_field(
                        name="> Online User", value=f"プレーヤー数:{len(sv_us)+us}人\n```{user}```\n==========", inline=False)
                else:
                    embed.add_field(
                        name="> Online User", value=":information_source:オンラインユーザーはいません。\n==========", inline=False)
            else:
                embed.add_field(
                    name="> Online User", value=":information_source:オンラインユーザーはいません。\n==========", inline=False)
        elif type == 1:
            embed.add_field(name="> Online User",
                            value=f"```{sv_us}```", inline=False)
    except BaseException as err:
        if str(err) == "timed out":
            if type == 0:
                embed.add_field(
                    name=f"> {sv_nm}", value=":ng:サーバーに接続できませんでした。(タイムアウト)\n==========", inline=False)
            if type == 1:
                embed.add_field(name=f"> {sv_nm}",
                                value=f"```{err}```", inline=False)
        else:
            logging.error(
                f"an error has occured during ServerStatus checking\n{err}")
            if type == 0:
                embed.add_field(
                    name=f"> {sv_nm}", value=":x:不明なエラーが発生しました。\n==========", inline=False)
            if type == 1:
                embed.add_field(name=f"> {sv_nm}",
                                value=f"```{err}```", inline=False)
    return True

# Bool返すタイプ


def ss_bool(g_id, n):
    sv_ad = n_fc.steam_server_list[g_id][f"{n}_ad"]
    for _ in range(3):
        try:
            if ip_check(sv_ad[0]):
                if web_api.server_status(sv_ad[0], sv_ad[1]) == False:
                    continue
            sv_dt = RetryInfo(sv_ad, 3)
            if sv_dt is None:
                raise TimeoutError("timed out")
            a2s.players(sv_ad)
        except BaseException:
            pass
        else:
            return True
    else:
        return False

# embed
# サーバーのステータスをチェックする


def ss_pin_embed(embed, g_id, n):
    sv_ad = n_fc.steam_server_list[g_id][f"{n}_ad"]
    sv_nm = n_fc.steam_server_list[g_id][f"{n}_nm"]
    sv_dt = "None"
    try:
        if ip_check(sv_ad[0]):
            if web_api.server_status(sv_ad[0], sv_ad[1]) == False:
                embed.add_field(
                    name=f"> {sv_nm}", value=":ng:オフライン\n==========", inline=False)
                return
        sv_dt = RetryInfo(sv_ad, 3)
        if sv_dt is None:
            raise TimeoutError("timed out")
        embed.add_field(name=f"> {sv_dt.server_name} - {sv_dt.map_name}",
                        value=":white_check_mark:オンライン", inline=False)
        user = ""
        sv_us = a2s.players(sv_ad)
        us = 0
        if sv_us != []:
            for i in range(len(sv_us)):
                user_add = str(sv_us[i].name)
                user_time = int(sv_us[i].duration/60)
                if user_time >= 60:
                    user_time = f"{int(user_time // 60)}時間{int(user_time % 60)}"
                if user_add != "":
                    user = user + f"\n{user_add} | {user_time}分"
                else:
                    us = us - 1
            if user == "":
                embed.add_field(
                    name="> Online User", value=":information_source:オンラインユーザーはいません。\n==========", inline=False)
            else:
                embed.add_field(
                    name="> Online User", value=f"プレーヤー数:{len(sv_us)+us}人\n```{user}```\n==========", inline=False)
        else:
            embed.add_field(
                name="> Online User", value=":information_source:オンラインユーザーはいません。\n==========", inline=False)
    except BaseException as err:
        if str(err) == "timed out":
            embed.add_field(
                name=f"> {sv_nm}", value=":ng:サーバーに接続できませんでした。(タイムアウト)\nサーバーがオンラインの可能性はあります。\n==========", inline=False)
        else:
            logging.error(
                f"an error has occured during ServerStatus checking\n{err}")
            embed.add_field(
                name=f"> {sv_nm}", value=":x:不明なエラーが発生しました。\n==========", inline=False)
    return True
