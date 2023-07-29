import asyncio
import enum

import a2s

from typing import TypedDict, Any


# 主にサーバーステータスを取得するコード

# # ステータスチェック中にメッセージ返信ができないものを修正する(Created by tasuren)
# async def server_check_loop(loop, g_id, n):
#     return await loop.run_in_executor(
#         None, ss_bool, g_id, n
#     )


class EmbedType(enum.Enum):
    NORMAL = 0
    DETAIL = 1

class Server(TypedDict):
    """
    サーバーの情報が入った辞書です。

    Attributes
    ----------
    _id : Any
        MongoDBのドキュメントで使用されているIDです。
    sv_ad : list[str | int]
        サーバーのアドレスです。
    server_id : int
        表示用に管理されているIDです。
    sv_nm : str
        サーバーの名前です。
    """
    _id: Any
    sv_ad: list[str | int]
    server_id: int
    sv_nm: str

class EmbedField(TypedDict):
    name: str
    value: str
    inline: bool


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

async def server_check(server: Server, type: EmbedType) -> EmbedField:
    """
    サーバーのステータスをチェックします。

    Parameters
    ----------
    server : Server
        サーバーの情報が入った辞書です。
    type : EmbedType
        Embedのタイプです。EmbedType.NORMALなら通常のEmbed、EmbedType.DETAILなら詳細なEmbedを返します。

    Returns
    -------
    EmbedField
        Embedのフィールドです。
    """
    try:
        sv_ad: tuple[str, int] = tuple(server["sv_ad"]) # type: ignore
        sv_nm = server["sv_nm"]
    except Exception:
        return {
            "name": "サーバーはセットされていません。",
            "value": "`n!ss list`でサーバーリストを確認してみましょう！",
            "inline": False
        }
    sv_dt = None
    sv_dt = await RetryInfo(sv_ad, 5)
    if sv_dt is None:
        if type == EmbedType.NORMAL:
            return {
                "name": f"> {sv_nm}",
                "value": ":octagonal_sign: サーバーに接続できませんでした。",
                "inline": False
            }
        elif type == EmbedType.DETAIL:
            return {
                "name": f"> {sv_nm}",
                "value": "`An error has occrred during checking server status.`\n`Processing [RetryInfo]`",
                "inline": False
            }
    if type == EmbedType.NORMAL:
        result = {
            "name": f"> {sv_dt.server_name} - {sv_dt.map_name}",
            "value": f":white_check_mark: オンライン `{round(sv_dt.ping*1000, 2)}`ms",
        }
    elif type == EmbedType.DETAIL:
        result = {
            "name": f"> {sv_dt.server_name} - {sv_dt.map_name}",
            "value": f"```{sv_dt}```",
        }
    sv_us = await RetryPlayers(sv_ad, 5)
    if sv_us is None:
        if type == EmbedType.NORMAL:
            return {
                "name": result["name"],
                "value": f"{result['value']}\nプレイヤー情報が取得できませんでした。",
                "inline": False,
            }
        elif type == EmbedType.DETAIL:
            return {
                "name": result["name"],
                "value": f"{result['value']}\n`An error has occurred during checking online player.`",
                "inline": False,
            }
    if type == EmbedType.NORMAL:
        if sv_us != []:
            users = [f"{u.name} | {f'{int(t // 60)}時間{int(t % 60)}' if (t := int(u.duration / 60)) >= 60 else t}分" for u in sv_us if u.name != ""]
            user = "\n".join(users)
            if user != "":
                return {
                    "name": result["name"],
                    "value": (
                        f"{result['value']}\n"
                        f"プレーヤー数:`{len(users)}/{sv_dt.max_players}`人"
                        f"```{user}```"
                    ),
                    "inline": False,
                }
            else:
                return {
                    "name": result["name"],
                    "value": f"{result['value']}\n:information_source: オンラインユーザーはいません。",
                    "inline": False,
                }
        else:
            return {
                "name": result["name"],
                "value": f"{result['value']}\n:information_source: オンラインユーザーはいません。",
                "inline": False,
            }
    elif type == EmbedType.DETAIL:
        return {
            "name": result["name"],
            "value": f"{result['value']}\n```{sv_us}```",
            "inline": False,
        }


# embed
# サーバーのステータスをチェックする

async def ss_pin_embed(server: Server) -> EmbedField:
    sv_ad: tuple[str, int] = tuple(server["sv_ad"]) # type: ignore
    sv_nm = server["sv_nm"]
    sv_dt = await RetryInfo(sv_ad, 5)
    if sv_dt is None:
        return {
            "name": f"> {sv_nm}",
            "value": ":octagonal_sign: サーバーに接続できませんでした。",
            "inline": False
        }
    result = {
        "name": f"> {sv_dt.server_name} - {sv_dt.map_name}",
        "value": f":white_check_mark: オンライン `{round(sv_dt.ping*1000, 2)}`ms",
    }
    sv_us = await RetryPlayers(sv_ad, 5)
    if sv_us is None:
        return {
            "name": result["name"],
            "value": f"{result['value']}\nプレイヤー情報が取得できませんでした。",
            "inline": False,
        }
    if sv_us != []:
        users = [f"{u.name} | {f'{int(t // 60)}時間{int(t % 60)}' if (t := int(u.duration / 60)) >= 60 else t}分" for u in sv_us if u.name != ""]
        user = "\n".join(users)
        if user != "":
            return {
                "name": result["name"],
                "value": (
                    f"{result['value']}\n"
                    f"プレーヤー数:`{len(users)}/{sv_dt.max_players}`人"
                    f"```{user}```"
                ),
                "inline": False,
            }
        else:
            return {
                "name": result["name"],
                "value": f"{result['value']}\n:information_source: オンラインユーザーはいません。",
                "inline": False,
            }
    else:
        return {
            "name": result["name"],
            "value": f"{result['value']}\n:information_source: オンラインユーザーはいません。",
            "inline": False,
        }
