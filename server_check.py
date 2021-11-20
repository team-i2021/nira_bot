# coding: utf-8
import n_cmd
import asyncio
import status_check
import a2s

# 主にサーバーステータスを取得するコード

# ステータスチェック中にメッセージ返信ができないものを修正する(Created by tasuren)
async def server_check_async(loop, embed, type, g_id, n):
    return await loop.run_in_executor(
        None, server_check, embed, type, g_id, n
    )

# サーバーのステータスをチェックする
def server_check(embed, type, g_id, n):
    try:
        sv_ad = n_cmd.steam_server_list[g_id][f"{n}_ad"]
        sv_nm = n_cmd.steam_server_list[g_id][f"{n}_nm"]
    except BaseException:
        embed.add_field(name=f"サーバーは{n}にはセットされていません。", value="`n!ss list`でサーバーリストを確認してみましょう！", inline=False)
        return
    sv_dt = "None"
    try:
        if status_check.server_status(sv_ad[0], sv_ad[1]) == False:
            if type == 0:
                embed.add_field(name=f"> {sv_nm}", value=":ng:Steam WEB APIでサーバーが認識されていません。\n==========", inline=False)
            if type == 1:
                embed.add_field(name=f"> {sv_nm}", value=f"```Steam WEB APIによる未然ストップ```", inline=False)
            return True
        sv_dt = a2s.info(sv_ad)
        if type == 0:
            embed.add_field(name=f"> {sv_nm}", value=":white_check_mark:Success!", inline=False)
        elif type == 1:
            embed.add_field(name=f"> {sv_nm}", value=f"```{sv_dt}```", inline=False)
        user = ""
        sv_us = a2s.players(sv_ad)
        if type == 0:
            if a2s.players(sv_ad) != []:
                sv_users_str = str(a2s.players(sv_ad)).replace("[", "").replace("]", "")
                sv_users_str = sv_users_str[7:]
                sv_users_str = sv_users_str + ", Player("
                sv_users_list = sv_users_str.split("), Player(")
                for i in range(len(a2s.players(sv_ad))):
                    sp_info = sv_users_list[-2]
                    splited = sp_info.split(", ", 4)[1]
                    user_add = splited.replace("name='", "").replace("'", "")
                    if user_add != "":
                        user = user + "\n" + f"```{user_add}```"
                    sv_users_list.pop()
                if user == "":
                    user = "（ユーザーデータが取得出来ませんでした。）"
                embed.add_field(name="> Online User", value=f"ユーザー数:{len(a2s.players(sv_ad))}人{user}\n==========", inline=False)
            else:
                embed.add_field(name="> Online User", value=":information_source:オンラインユーザーはいません。\n==========", inline=False)
        elif type == 1:
            embed.add_field(name="> Online User", value=f"```{sv_us}```", inline=False)
    except BaseException as err:
        print(err)
        if str(err) == "timed out":
            if type == 0:
                embed.add_field(name=f"> {sv_nm}", value=":ng:サーバーに接続できませんでした。\n==========", inline=False)
            if type == 1:
                embed.add_field(name=f"> {sv_nm}", value=f"```{err}```", inline=False)
        else:
            if type == 0:
                embed.add_field(name=f"> {sv_nm}", value=":x:不明なエラーが発生しました。\n==========", inline=False)
            if type == 1:
                embed.add_field(name=f"> {sv_nm}", value=f"```{err}```", inline=False)
    return True