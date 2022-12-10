import asyncio
import datetime
import logging
import math
import re
import sys
import traceback

import a2s

from util import database
import util.web_api as web_api

# 主にサーバーステータスを取得するコード

class steam_server:
    name = "steam_server"
    value = {}
    default = {}
    value_type = database.CHANNEL_VALUE


# ステータスチェック中にメッセージ返信ができないものを修正する(Created by tasuren)
async def server_check_loop(loop, g_id, n):
    return await loop.run_in_executor(
        None, ss_bool, g_id, n
    )


async def RetryInfo(address: tuple, count: int) -> a2s.SourceInfo or None:
    """サーバーのステータスを取得しますが、その際`count`回リトライします。"""
    for _ in range(count):
        try:
            info = await a2s.ainfo(address)
            return info
        except Exception as err:
            await asyncio.sleep(1)
    return None


async def RetryPlayers(address: tuple, count: int) -> a2s.Player or None:
    """サーバーのユーザー情報を取得しますが、その際`count`回リトライします。"""
    for _ in range(count):
        try:
            players = await a2s.aplayers(address)
            return players
        except Exception as err:
            await asyncio.sleep(1)
    return None

# サーバーのステータスをチェックする


async def server_check(client, embed, type, g_id, n):
    try:
        await database.default_pull(client, steam_server)
        sv_ad = tuple(steam_server.value[g_id][f"{n}_ad"])
        sv_nm = steam_server.value[g_id][f"{n}_nm"]
    except Exception:
        embed.add_field(
            name=f"サーバーは{n}にはセットされていません。",
            value=f"`n!ss list`でサーバーリストを確認してみましょう！",
            inline=False
        )
        return
    sv_dt = None
    sv_dt = await RetryInfo(sv_ad, 5)
    if sv_dt is None:
        if type == 0:
            embed.add_field(
                name=f"> {sv_nm}",
                value=":ng:サーバーに接続できませんでした。",
                inline=False
            )
        elif type == 1:
            embed.add_field(
                name=f"> {sv_nm}",
                value=f"`An error has occrred during checking server status.`",
                inline=False
            )
        return True
    if type == 0:
        embed.add_field(
            name=f"> {sv_dt.server_name} - {sv_dt.map_name}",
            value=f":white_check_mark:オンライン `{round(sv_dt.ping*1000,2)}`ms",
            inline=False
        )
    elif type == 1:
        embed.add_field(
            name=f"> {sv_dt.server_name} - {sv_dt.map_name}",
            value=f"```{sv_dt}```",
            inline=False
        )
    user = ""
    sv_us = await RetryPlayers(sv_ad, 5)
    if sv_us is None:
        if type == 0:
            embed.add_field(
                name=f"> Online Player",
                value="プレイヤー情報が取得できませんでした。",
                inline=False
            )
        elif type == 1:
            embed.add_field(
                name=f"> Online Player",
                value=f"`An error has occurred during checking online player.`",
                inline=False
            )
        return True
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
                    name="> Online Player", value=f"プレーヤー数:`{len(sv_us)+us}/{sv_dt.max_players}`人\n```{user}```\n==========", inline=False)
            else:
                embed.add_field(
                    name="> Online Player", value=":information_source:オンラインユーザーはいません。\n==========", inline=False)
        else:
            embed.add_field(
                name="> Online Player", value=":information_source:オンラインユーザーはいません。\n==========", inline=False)
    elif type == 1:
        embed.add_field(name="> Online Player",
                        value=f"```{sv_us}```", inline=False)
    return True

# Bool返すタイプ


async def ss_bool(client, g_id, n):
    await database.default_pull(client, steam_server)
    sv_ad = tuple(steam_server.value[g_id][f"{n}_ad"])
    for _ in range(3):
        try:
            sv_dt = await RetryInfo(sv_ad, 5)
            if sv_dt is None:
                raise TimeoutError("timed out")
            sv_pl = RetryPlayers(sv_ad)
            if sv_pl is None:
                raise TimeoutError("timed out")
        except Exception:
            pass
        else:
            return True
    else:
        return False

# embed
# サーバーのステータスをチェックする


async def ss_pin_embed(client, embed, g_id, n):
    await database.default_pull(client, steam_server)
    sv_ad = tuple(steam_server.value[g_id][f"{n}_ad"])
    sv_nm = steam_server.value[g_id][f"{n}_nm"]
    sv_dt = await RetryInfo(sv_ad, 5)
    if sv_dt is None:
        embed.add_field(
            name=f"> {sv_nm}",
            value=":ng:サーバーに接続できませんでした。",
            inline=False
        )
        return True
    embed.add_field(
        name=f"> {sv_dt.server_name} - {sv_dt.map_name}",
        value=f":white_check_mark:オンライン `{round(sv_dt.ping*1000,2)}`ms",
        inline=False
    )
    user = ""
    sv_us = await RetryPlayers(sv_ad, 5)
    if sv_us is None:
        embed.add_field(
            name=f"> Online Player",
            value="プレイヤー情報が取得できませんでした。",
            inline=False
        )
        return True
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
        if user != "":
            embed.add_field(
                name="> Online Player", value=f"プレーヤー数:`{len(sv_us)+us}/{sv_dt.max_players}`人\n```{user}```\n==========", inline=False)
        else:
            embed.add_field(
                name="> Online Player", value=":information_source:オンラインユーザーはいません。\n==========", inline=False)
    else:
        embed.add_field(
            name="> Online Player", value=":information_source:オンラインユーザーはいません。\n==========", inline=False)
    return True
