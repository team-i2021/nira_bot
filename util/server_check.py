import asyncio

import a2s
import nextcord

# 主にサーバーステータスを取得するコード


# # ステータスチェック中にメッセージ返信ができないものを修正する(Created by tasuren)
# async def server_check_loop(loop, g_id, n):
#     return await loop.run_in_executor(
#         None, ss_bool, g_id, n
#     )


async def RetryInfo(address: tuple[str, int], count: int = 3) -> a2s.SourceInfo | a2s.GoldSrcInfo | None:
    """サーバーのステータスを取得しますが、その際`count`回リトライします。"""
    for _ in range(count):
        try:
            info = await a2s.ainfo(address)
            return info
        except Exception:
            await asyncio.sleep(1)
    return None


async def RetryPlayers(address: tuple[str, int], count: int = 3) -> list[a2s.Player] | None:
    """サーバーのユーザー情報を取得しますが、その際`count`回リトライします。"""
    for _ in range(count):
        try:
            players: list[a2s.Player] = await a2s.aplayers(address)
            return [pl for pl in players if pl.name != ""]
        except Exception:
            await asyncio.sleep(1)
    return None


# サーバーのステータスをチェックする


async def server_check(server: dict[str, str | list[str | int]], embed: nextcord.Embed, type):
    try:
        sv_ad: tuple[str, int] = tuple(server["sv_ad"])
        sv_nm = server["sv_nm"]
    except Exception:
        embed.insert_field_at(
            index=server["server_id"] - 1,
            name="サーバーはセットされていません。",
            value="`n!ss list`でサーバーリストを確認してみましょう！",
            inline=False
        )
        return
    sv_dt = None
    sv_dt = await RetryInfo(sv_ad, 5)
    if sv_dt is None:
        if type == 0:
            embed.insert_field_at(
                index=server["server_id"] - 1,
                name=f"> {sv_nm}",
                value=":ng:サーバーに接続できませんでした。",
                inline=False,
            )
        elif type == 1:
            embed.insert_field_at(
                index=server["server_id"] - 1,
                name=f"> {sv_nm}",
                value="`An error has occrred during checking server status.`",
                inline=False,
            )
        return True
    if type == 0:
        result = {
            "name": f"> {sv_dt.server_name} - {sv_dt.map_name}",
            "value": f":white_check_mark:オンライン `{round(sv_dt.ping*1000, 2)}`ms",
        }
    elif type == 1:
        result = {
            "name": f"> {sv_dt.server_name} - {sv_dt.map_name}",
            "value": f"```{sv_dt}```",
        }
    else:
        raise ValueError
    sv_us = await RetryPlayers(sv_ad, 5)
    if sv_us is None:
        if type == 0:
            embed.insert_field_at(
                index=server["server_id"] - 1,
                name=result["name"],
                value=f"{result['value']}\nプレイヤー情報が取得できませんでした。",
                inline=False,
            )
        elif type == 1:
            embed.insert_field_at(
                index=server["server_id"] - 1,
                name=result["name"],
                value=f"{result['value']}\n`An error has occurred during checking online player.`",
                inline=False,
            )
        return True
    if type == 0:
        if sv_us != []:
            users = [f"{u.name} | {f'{int(t // 60)}時間{int(t % 60)}' if (t := int(u.duration / 60)) >= 60 else t}分" for u in sv_us if u.name != ""]
            user = "\n".join(users)
            if user != "":
                embed.insert_field_at(
                    index=server["server_id"] - 1,
                    name=result["name"],
                    value=(
                        f"{result['value']}\n"
                        f"プレーヤー数:`{len(users)}/{sv_dt.max_players}`人"
                        f"```{user}```"
                    ),
                    inline=False,
                )
            else:
                embed.insert_field_at(
                    index=server["server_id"] - 1,
                    name=result["name"],
                    value=f"{result['value']}\n:information_source:オンラインユーザーはいません。",
                    inline=False,
                )
        else:
            embed.insert_field_at(
                index=server["server_id"] - 1,
                name=result["name"],
                value=f"{result['value']}\n:information_source:オンラインユーザーはいません。",
                inline=False,
            )
    elif type == 1:
        embed.insert_field_at(
            index=server["server_id"] - 1,
            name=result["name"],
            value=f"{result['value']}```{sv_us}```",
            inline=False,
        )
    return True

# embed
# サーバーのステータスをチェックする

async def ss_pin_embed(server: dict[str, str | list[str | int]], embed: nextcord.Embed):
    sv_ad: tuple[str, int] = tuple(server["sv_ad"])
    sv_nm = server["sv_nm"]
    sv_dt = await RetryInfo(sv_ad, 5)
    if sv_dt is None:
        embed.insert_field_at(
            index=server["server_id"] - 1,
            name=f"> {sv_nm}",
            value=":ng:サーバーに接続できませんでした。",
            inline=False,
        )
        return True
    result = {
        "name": f"> {sv_dt.server_name} - {sv_dt.map_name}",
        "value": f":white_check_mark:オンライン `{round(sv_dt.ping*1000, 2)}`ms",
    }
    sv_us = await RetryPlayers(sv_ad, 5)
    if sv_us is None:
        embed.insert_field_at(
            index=server["server_id"] - 1,
            name=result["name"],
            value=f"{result['value']}\nプレイヤー情報が取得できませんでした。",
            inline=False,
        )
        return True
    if sv_us != []:
        users = [f"{u.name} | {f'{int(t // 60)}時間{int(t % 60)}' if (t := int(u.duration / 60)) >= 60 else t}分" for u in sv_us if u.name != ""]
        user = "\n".join(users)
        if user != "":
            embed.insert_field_at(
                index=server["server_id"] - 1,
                name=result["name"],
                value=(
                    f"{result['value']}\n"
                    f"プレーヤー数:`{len(users)}/{sv_dt.max_players}`人"
                    f"```{user}```"
                ),
                inline=False,
            )
        else:
            embed.insert_field_at(
                index=server["server_id"] - 1,
                name=result["name"],
                value=f"{result['value']}\n:information_source:オンラインユーザーはいません。\n==========",
                inline=False,
            )
    else:
        embed.insert_field_at(
            index=server["server_id"] - 1,
            name=result["name"],
            value=f"{result['value']}\n:information_source:オンラインユーザーはいません。\n==========",
            inline=False,
        )
    return True
